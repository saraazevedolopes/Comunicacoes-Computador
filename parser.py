import json


# Retorna os dados como uma lista
def parse(message: bytes):
    fields : list = []
    bits = ''.join(f'{byte:08b}' for byte in message) # converte bytes para bits
    print(bits)

    # Extrai partes específicas da mensagem
    fields.append(int(bits[:5], 2))            # Primeiros 5 bits para o ID do agente
    fields.append(int(bits[5:8], 2))           # Próximos 3 bits para o tipo de mensagem
    fields.append(int(bits[8:16], 2))          # Próximos 8 bits para o número de sequência

    
    if fields[1] == 0:
        fields.append(int(bits[8:16], 2))      # Próximos 8 bits para o número de sequência
        print(f"O seq é {fields[2]}")
    else:
        print("Recebi um ACK")
        print(f"O ACK é {fields[2]}")

    print(f"o ID do agente é o {fields[0]}")
    print(f"a message type é {fields[1]}")
    
    
    return fields # 2 indica que o que está a receber é binário

def parse_tasks(agent_name : str) -> dict: # retorna um dicionário com as tarefas do agente
    data : dict = dict()

    with open("agent" + agent_name + ".json", "r") as file_json: # with garante que há um close do open
            data = json.load(file_json)

    return data