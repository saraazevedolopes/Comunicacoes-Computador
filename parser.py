import json
from Message_type import Message_type

# Retorna os dados como uma lista
def parse(message: bytes):
    fields : list = []
    bits = ''.join(f'{byte:08b}' for byte in message) # converte bytes para bits
    #print(bits)

    # Extrai partes específicas da mensagem
    fields.append(int(bits[:5], 2))            # Primeiros 5 bits para o ID do agente
    fields.append(int(bits[5:8], 2))           # Próximos 3 bits para o tipo de mensagem
    fields.append(int(bits[8:16], 2))          # Próximos 8 bits para o número de sequência
  
    if fields[1] == Message_type.ACK.value:
        print("Recebi um ACK")
        print(f"O ACK é {fields[2]}")
    elif fields[1] == Message_type.TASK.value:
        print(f"Recebi uma tarefa com seq = {fields[2]}")
        fields.append(int(bits[16:21], 2))     # Task ID
        fields.append(int(bits[21:29], 2))     # Frequency
        fields.append(int(bits[29:45], 2))     # Threshold
        fields.append(int(bits[45:48], 2))     # Task Type

        print(f"""Os fields são:
        Agent_id: {fields[0]}
        Message_type: {fields[1]}
        Seq: {fields[2]}
        Task_ID: {fields[3]}
        Frequency: {fields[4]}
        Threshold: {fields[5]}
        Task_type: {fields[6]}""")

        if fields[6] == 2:
            # Obter os 32 bits que representam o endereço IP
            ip_bits = bits[48:80]

            # Dividir em grupos de 8 bits
            octets = [ip_bits[i:i+8] for i in range(0, 32, 8)]

            # Converter cada grupo de bits para decimal
            octets_decimal = [int(octet, 2) for octet in octets]

            # Formatar no estilo "xxx.xxx.xxx.xxx"
            ip_address = ".".join(map(str, octets_decimal))

            fields.append(ip_address)
            
            # Destination Address
            print(f"Endereço IP: {ip_address}")

        """
        fields.append(bin(int(args[0]))[2:].zfill(5)) # task id
        fields.append(bin(int(args[1]["frequency"]))[2:].zfill(8)) # freq
        fields.append(bin(int(args[1]["threshold"]))[2:].zfill(16)) # threshold
        fields.append(bin(int(args[1]["task_type"]))[2:].zfill(3)) # task_type"""
    elif fields[1] == Message_type.METRIC.value:
        print(f"Recebi uma métrica")
    elif fields[1] == Message_type.END.value:
        print(f"Recebi um END")

    #print(f"o ID do agente é o {fields[0]}")
    #print(f"a message type é {fields[1]}")
    
    
    return fields # 2 indica que o que está a receber é binário

def parse_tasks(agent_name : str) -> dict: # retorna um dicionário com as tarefas do agente
    data : dict = dict()
    with open("agent" + agent_name + ".json", "r") as file_json: # with garante que há um close do open
            data = json.load(file_json)
    return data
