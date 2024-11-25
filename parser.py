import json
from Message_type import Message_type
import logger

# Interpreta uma mensagem recebida em formato binário e extrai os campos relevantes para uma lista
def parse_tcp(message: bytes) -> list:
    fields : list = []

    # Converte bytes para bits
    bits = ''.join(f'{byte:08b}' for byte in message) 

    # Extrai partes da mensagem
    fields.append(int(bits[:5], 2))     # Primeiros 5 bits para o ID do agente
    fields.append(int(bits[5:8], 2))  # Task Type
    fields.append(int(bits[8:16], 2))     # Task ID
   

    logger.log(f"""Os fields são:
    Agent_id: {fields[0]}
    Task_ID: {fields[1]}
    Task_type: {fields[2]}\n""")

    # Task_type == 0,1,2 -> CPU, RAM, ou Latência
    if fields[1] in [0,1,2]:
        fields.append(int(bits[16:32], 2))
    elif fields[1] == 3:
        fields.append(int(bits[16:32], 2))
        fields.append(chr(int(bits[32:40], 2)))
    else:
        fields.append(int(bits[16:24], 2))
    
    print(f"ALERTFLOW FIELDS RECEBIDOS: {fields}")

    return fields 

# Interpreta uma mensagem recebida em formato binário e extrai os campos relevantes para uma lista
def parse(message: bytes) -> list:
    fields : list = []

    # Converte bytes para bits
    bits = ''.join(f'{byte:08b}' for byte in message) 

    # Extrai partes da mensagem
    fields.append(int(bits[:5], 2))            # Primeiros 5 bits para o ID do agente
    fields.append(int(bits[5:8], 2))           # Próximos 3 bits para o tipo de mensagem
    fields.append(int(bits[8:24], 2))          # Próximos 8 bits para o número de sequência
    
    # Se for um ACK
    if fields[1] == Message_type.ACK.value: 
        logger.log("Recebi um ACK")
        logger.log(f"O ACK é {fields[2]}")

    # Se for uma Task
    elif fields[1] == Message_type.TASK.value: 
        logger.log(f"Recebi uma tarefa com seq = {fields[2]}")
        fields.append(int(bits[24:29], 2))     # Task ID
        fields.append(int(bits[29:37], 2))     # Frequency
        fields.append(int(bits[37:53], 2))     # Threshold
        fields.append(int(bits[53:56], 2))     # Task Type

        logger.log(f"""Os fields são:
        Agent_id: {fields[0]}
        Message_type: {fields[1]}
        Seq: {fields[2]}
        Task_ID: {fields[3]}
        Frequency: {fields[4]}
        Threshold: {fields[5]}
        Task_type: {fields[6]}\n""")

        # Task_type == 2 -> Latência
        if fields[6] == 2: 

            # Obter os 32 bits que representam o endereço IP
            ip_bits = bits[56:88]

            # Dividir em grupos de 8 bits
            octets = [ip_bits[i:i+8] for i in range(0, 32, 8)]

            # Converter cada grupo de bits para decimal
            octets_decimal = [int(octet, 2) for octet in octets]

            # Formatar no estilo "xxx.xxx.xxx.xxx"
            ip_address = ".".join(map(str, octets_decimal))

            fields.append(ip_address)
            logger.log(f"Endereço IP: {ip_address}")
        
        # Task_type == 3 -> Throughput 
        elif fields[6] == 3:

            is_server = int(bits[56:64],2)
            fields.append(is_server)
            ip_bits = bits[64:96]

            # Dividir em grupos de 8 bits
            octets = [ip_bits[i:i+8] for i in range(0, 32, 8)]

            # Converter cada grupo de bits para decimal
            octets_decimal = [int(octet, 2) for octet in octets]

            # Formatar no estilo "xxx.xxx.xxx.xxx"
            destination = ".".join(map(str, octets_decimal))
            print(f"O ENDEREÇO É {destination}")
            fields.append(destination)
                

        # Task_type == 4 -> Interfaces 
        elif fields[6] == 4:
            fields.append(str(bits[56:136]))
            
            # Divide em blocos de 8 bits
            chunks = [bits[56:136][i:i+8] for i in range(0, 80, 8)]

            # Converte cada bloco de 8 bits num carácter
            original_string = ''.join(chr(int(chunk, 2)) for chunk in chunks)

            # Remove possíveis espaços adicionais adicionados por ljust ou rjust
            original_string = original_string.strip()

    # Se for uma Metric
    elif fields[1] == Message_type.METRIC.value:
        task_id = int(bits[24:29], 2)
        task_type = int(bits[29:32], 2)

        # CPU, RAM, latência e interfaces -> apenas 1 valor
        if task_type in [0,1,2,4]: 
            metric = int(bits[32:48], 2)  

        # Throughput (inclui Largura de banda, jitter e perdas) -> 3 valores
        else:  
            metric = list() 
            metric.append(int(bits[32:48]))
            metric.append(str(bits[48:56]))
            metric.append(int(bits[56:72]))
            metric.append(int(bits[72:80]))
            
        fields.append(task_id) 
        fields.append(task_type) 
        fields.append(metric)

        logger.log(f"Recebi uma métrica com {task_id} {task_type} {metric}")
    
    # Se for um End
    elif fields[1] == Message_type.END.value:
        logger.log(f"Recebi um END")
        # TODO
    
    return fields 

# Carrega tarefas atribuídas a um agente a partir de um ficheiro JSON.
def parse_tasks(agent_name : str) -> dict:
    data : dict = dict()
    
    with open("agent" + agent_name + ".json", "r") as file_json: # with garante que há um close do open
            data = json.load(file_json)
    
    # Dicionário com as tarefas do agente
    return data
