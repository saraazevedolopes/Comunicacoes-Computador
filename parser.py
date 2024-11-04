import struct
import json


HEADER_FORMAT = "6s H H 15s 500s"

def parse(message: bytes):
    # Desempacota a mensagem usando o HEADER_FORMAT
    unpacked_data = struct.unpack(HEADER_FORMAT, message)
    
    # Extrai e converte cada campo para o tipo correto
    server_str = unpacked_data[0].decode('ascii').rstrip('\x00')
    seq = unpacked_data[1]
    ack = unpacked_data[2]
    task_name = unpacked_data[3].decode('ascii').rstrip('\x00')
    task_contents_str = unpacked_data[4].decode('ascii').rstrip('\x00')
    
    # Converte a string JSON de volta para um dicionário (se `task_contents` foi serializado com `json.dumps`)
    try:
        task_contents = json.loads(task_contents_str)
    except json.JSONDecodeError:
        task_contents = {}  # Trata erro caso a string JSON esteja truncada ou inválida
    
    # Retorna os dados como uma lista
    return [server_str, seq, ack, task_name, task_contents]

def parse_tasks(agent_name : str) -> dict: # retorna um dicionário com as tarefas do agente
    data : dict = dict()

    with open(agent_name+".json", "r") as file_json: # with garante que há um close do open
            data = json.load(file_json)

    return data