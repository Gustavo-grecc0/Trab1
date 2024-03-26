from flask import Flask, jsonify, request, g
import sqlite3

app = Flask(__name__)

def obter_conexao():
    if 'conexao_db' not in g:
        g.conexao_db = sqlite3.connect('enquetes.db')
        g.cursor_db = g.conexao_db.cursor()
    return g.conexao_db, g.cursor_db

# Criação da tabela de pesquisas
@app.before_request
def criar_tabelas():
    conexao, cursor = obter_conexao()
    cursor.execute('''CREATE TABLE IF NOT EXISTS pesquisas
                     (id_pesquisa INTEGER PRIMARY KEY AUTOINCREMENT, titulo_pesquisa TEXT, descricao_pesquisa TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS opcoes_pesquisa
                     (id_opcao INTEGER PRIMARY KEY AUTOINCREMENT, id_pesquisa INTEGER, texto_opcao TEXT, quantidade_votos INTEGER DEFAULT 0, FOREIGN KEY(id_pesquisa) REFERENCES pesquisas(id_pesquisa))''')
    conexao.commit()

# 1. Criar Pesquisa
@app.route('/api/pesquisas', methods=['POST'])
def criar_pesquisa():
    dados_recebidos = request.get_json()
    titulo_pesquisa = dados_recebidos.get('titulo')
    descricao_pesquisa = dados_recebidos.get('descricao')

    if not titulo_pesquisa or not descricao_pesquisa:
        return jsonify({'erro': 'Os campos título e descrição são obrigatórios.'}), 400

    conexao, cursor = obter_conexao()
    cursor.execute("INSERT INTO pesquisas (titulo_pesquisa, descricao_pesquisa) VALUES (?, ?)", (titulo_pesquisa, descricao_pesquisa))
    conexao.commit()
    return jsonify({'mensagem': 'Pesquisa criada com sucesso.'}), 201

# 2. Listar Pesquisas
@app.route('/api/pesquisas', methods=['GET'])
def listar_pesquisas():
    conexao, cursor = obter_conexao()
    cursor.execute("SELECT * FROM pesquisas")
    todas_pesquisas = cursor.fetchall()
    lista_pesquisas = []
    for pesquisa in todas_pesquisas:
        pesquisa_dict = {
            'id_pesquisa': pesquisa[0],
            'titulo_pesquisa': pesquisa[1],
            'descricao_pesquisa': pesquisa[2]
        }
        lista_pesquisas.append(pesquisa_dict)
    return jsonify(lista_pesquisas), 200

# 3. Obter detalhes de uma pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>', methods=['GET'])
def obter_pesquisa(id_pesquisa):
    conexao, cursor = obter_conexao()
    cursor.execute("SELECT * FROM pesquisas WHERE id_pesquisa = ?", (id_pesquisa,))
    pesquisa = cursor.fetchone()
    if pesquisa:
        pesquisa_dict = {
            'id_pesquisa': pesquisa[0],
            'titulo_pesquisa': pesquisa[1],
            'descricao_pesquisa': pesquisa[2]
        }
        return jsonify(pesquisa_dict), 200
    else:
        return jsonify({'erro': 'Pesquisa não encontrada.'}), 404

# 4. Votar em uma opção de pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>/votar', methods=['POST'])
def votar_pesquisa(id_pesquisa):
    dados_recebidos = request.get_json()
    id_opcao = dados_recebidos.get('id_opcao')

    if not id_opcao:
        return jsonify({'erro': 'O ID da opção é obrigatório.'}), 400

    conexao, cursor = obter_conexao()
    cursor.execute("UPDATE opcoes_pesquisa SET quantidade_votos = quantidade_votos + 1 WHERE id_opcao = ?", (id_opcao,))
    conexao.commit()
    return jsonify({'mensagem': 'Voto registrado com sucesso.'}), 200

# 5. Resultados de uma pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>/resultados', methods=['GET'])
def resultados_pesquisa(id_pesquisa):
    conexao, cursor = obter_conexao()
    cursor.execute("SELECT texto_opcao, quantidade_votos FROM opcoes_pesquisa WHERE id_pesquisa = ?", (id_pesquisa,))
    resultados = cursor.fetchall()
    if resultados:
        resultados_dict = []
        for resultado in resultados:
            resultado_dict = {
                'opcao': resultado[0],
                'votos': resultado[1]
            }
            resultados_dict.append(resultado_dict)
        return jsonify(resultados_dict), 200
    else:
        return jsonify({'erro': 'Pesquisa não encontrada ou sem opções.'}), 404

# 6. Visualizar opções de uma pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>/opcoes', methods=['GET'])
def listar_opcoes(id_pesquisa):
    conexao, cursor = obter_conexao()
    cursor.execute("SELECT texto_opcao FROM opcoes_pesquisa WHERE id_pesquisa = ?", (id_pesquisa,))
    opcoes = cursor.fetchall()
    if opcoes:
        lista_opcoes = [opcao[0] for opcao in opcoes]
        return jsonify(lista_opcoes), 200
    else:
        return jsonify({'erro': 'Pesquisa não encontrada ou sem opções.'}), 404

# 7. Adicionar a opção em uma pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>/opcoes', methods=['POST'])
def adicionar_opcao(id_pesquisa):
    dados_recebidos = request.get_json()
    texto_opcao = dados_recebidos.get('opcao')

    if not texto_opcao:
        return jsonify({'erro': 'O campo opção é obrigatório.'}), 400

    conexao, cursor = obter_conexao()
    cursor.execute("INSERT INTO opcoes_pesquisa (id_pesquisa, texto_opcao) VALUES (?, ?)", (id_pesquisa, texto_opcao))
    conexao.commit()
    return jsonify({'mensagem': 'Opção adicionada com sucesso.'}), 201

# 8. Deletar pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>', methods=['DELETE'])
def deletar_pesquisa(id_pesquisa):
    conexao, cursor = obter_conexao()
    cursor.execute("DELETE FROM pesquisas WHERE id_pesquisa = ?", (id_pesquisa,))
    conexao.commit()
    if cursor.rowcount > 0:
        return jsonify({'mensagem': 'Pesquisa deletada com sucesso.'}), 200
    else:
        return jsonify({'erro': 'Pesquisa não encontrada.'}), 404

# 9. Deletar uma opção de uma pesquisa
@app.route('/api/pesquisas/<int:id_pesquisa>/opcoes/<int:id_opcao>', methods=['DELETE'])
def deletar_opcao(id_pesquisa, id_opcao):
    conexao, cursor = obter_conexao()
    cursor.execute("DELETE FROM opcoes_pesquisa WHERE id_opcao = ? AND id_pesquisa = ?", (id_opcao, id_pesquisa))
    conexao.commit()
    if cursor.rowcount > 0:
        return jsonify({'mensagem': 'Opção deletada com sucesso.'}), 200
    else:
        return jsonify({'erro': 'Opção não encontrada.'}), 404

@app.teardown_appcontext
def fechar_conexao(erro):
    if hasattr(g, 'conexao_db'):
        g.conexao_db.close()

if __name__ == '__main__':
    app.run(debug=True)
