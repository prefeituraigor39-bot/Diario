from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

BASE_URL = "https://www.diariomunicipal.com.br/amm-mg"
SEARCH_URL = f"{BASE_URL}/pesquisar"
ENTIDADE = "760"
ORGAO = "1379"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def get_token():
    resp = session.get(SEARCH_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    inp = soup.find("input", {"name": "busca_avancada[_token]"})
    return inp["value"] if inp else ""


def buscar(palavra, data_inicio, data_fim):
    token = get_token()
    params = {
        "busca_avancada[entidadeUsuaria]": ENTIDADE,
        "busca_avancada[nome_orgao]": ORGAO,
        "busca_avancada[texto]": palavra,
        "busca_avancada[dataInicio]": data_inicio,
        "busca_avancada[dataFim]": data_fim,
        "busca_avancada[_token]": token,
    }
    resp = session.get(SEARCH_URL, params=params)
    soup = BeautifulSoup(resp.text, "html.parser")

    resultados = []
    for linha in soup.select("#datatable tbody tr"):
        links = linha.find_all("a")
        if len(links) < 2:
            continue
        href = links[0].get("href", "")
        if "/amm-mg/" not in href:
            continue
        codigo = href.split("/")[-1]
        titulo = links[1].text.strip()
        link = f"https://www.diariomunicipal.com.br/amm-mg/load/{codigo}"
        resultados.append({"titulo": titulo, "link": link})

    return resultados


@app.route("/buscar", methods=["GET"])
def buscar_endpoint():
    palavras_raw = request.args.get("palavras", "")
    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")

    if not palavras_raw:
        return jsonify({"erro": "Informe ao menos uma palavra-chave."}), 400

    palavras = [p.strip() for p in palavras_raw.split(",") if p.strip()]
    todos = []
    for palavra in palavras:
        todos.extend(buscar(palavra, data_inicio, data_fim))

    return jsonify({"total": len(todos), "resultados": todos})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
