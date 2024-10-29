import json
import pickle

def parse(message : bytes): # converte uma mensagem serializada em lista
    data : List = pickle.loads(message)
    
    return data


def parse_tasks(agent_name : str) -> dict: # retorna um dicionário com as tarefas do agente
    data : dict = dict()

    with open(agent_name+".json", "r") as file_json: # with garante que há um close do open
            data = json.load(file_json)

    return data