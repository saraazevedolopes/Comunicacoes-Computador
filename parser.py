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
    fields.append(int(bits[5:8], 2))    # Task Type
    fields.append(int(bits[8:16], 2))   # Task ID
   
    '''
    logger.log(f"""Os fields são:
    Agent_id: {fields[0]}
    Task_ID: {fields[1]}
    Task_type: {fields[2]}\n""")
    '''
    # Task_type == 0,1,2 -> CPU, RAM, ou Latência
    if fields[1] in [0,1,2]:
        fields.append(int(bits[16:32], 2))
    elif fields[1] == 3:
        iperf = list()
        iperf.append(int(bits[16:32], 2))
        iperf.append(chr(int(bits[32:40], 2)))
        iperf.append(int(bits[40:56], 2))
        iperf.append(int(bits[56:64], 2))
        if iperf[0] == 0 and iperf[2] == 0 and iperf[3] == 100:
            iperf = [-1,"DESTINATION UNREACHABLE"]
        fields.append(iperf)
    else:
        fields.append(int(bits[16:24], 2))

    return fields 

# Interpreta uma mensagem recebida em formato binário e extrai os campos relevantes para uma lista
def parse(message: bytes, server : bool, device_logger) -> list:
    fields : list = []

    # Converte bytes para bits
    bits = ''.join(f'{byte:08b}' for byte in message) 

    # Extrai partes da mensagem
    fields.append(int(bits[:5], 2))            # Primeiros 5 bits para o ID do agente
    fields.append(int(bits[5:8], 2))           # Próximos 3 bits para o tipo de mensagem
    fields.append(int(bits[8:24], 2))          # Próximos 8 bits para o número de sequência
    
    # Se for um ACK
    if fields[1] == Message_type.ACK.value: 
        if server:
            device_logger[fields[0]].debug(f"RECEIVED ACK SEQ={fields[2]}")
        else:
            device_logger.debug(f"RECEIVED ACK SEQ={fields[2]}")
        
    # Se for uma Task
    elif fields[1] == Message_type.TASK.value: 
        fields.append(int(bits[24:29], 2))     # Task ID
        fields.append(int(bits[29:32], 2))     # Task Type
        fields.append(int(bits[32:40], 2))     # Frequency
        
        if fields[4] == 3:
            threshold = []
            threshold.append(int(bits[40:56], 2))     # Threshold de throughput
            threshold.append(int(bits[56:72], 2))     # Threshold de jitter
            threshold.append(int(bits[72:80], 2))     # Threshold de losses
            fields.append(threshold)
        else:
            fields.append(int(bits[40:56], 2))     # Threshold
        '''
        logger.log(f"""Os fields são:
        Agent_id: {fields[0]}
        Message_type: {fields[1]}
        Seq: {fields[2]}
        Task_ID: {fields[3]}
        Task_type: {fields[4]}
        Frequency: {fields[5]}
        Threshold: {fields[6]}
        \n""")'''
        if fields[4] == 0:
            device_logger.info(f"RECEIVED TASK SEQ={fields[2]} LENGTH={len(message)} ID={fields[3]} TASK_TYPE=CPU FREQUENCY={fields[5]} THRESHOLD={fields[6]}")
        elif fields[4] == 1:
            device_logger.info(f"RECEIVED TASK SEQ={fields[2]} LENGTH={len(message)} ID={fields[3]} TASK_TYPE=RAM FREQUENCY={fields[5]} THRESHOLD={fields[6]}")
        # Task_type == 2 -> Latência
        elif fields[4] == 2: 

            # Obter os 32 bits que representam o endereço IP
            ip_bits = bits[56:88]

            # Dividir em grupos de 8 bits
            octets = [ip_bits[i:i+8] for i in range(0, 32, 8)]

            # Converter cada grupo de bits para decimal
            octets_decimal = [int(octet, 2) for octet in octets]

            # Formatar no estilo "xxx.xxx.xxx.xxx"
            ip_address = ".".join(map(str, octets_decimal))

            device_logger.info(f"RECEIVED TASK SEQ={fields[2]} LENGTH={len(message)} ID={fields[3]} TASK_TYPE=LATENCY DESTINATION={ip_address} FREQUENCY={fields[5]} THRESHOLD={fields[6]}")

            fields.append(ip_address)

        # Task_type == 3 -> Throughput 
        elif fields[4] == 3:

            is_server = int(bits[80:88],2)
            fields.append(is_server)
            ip_bits = bits[88:120]

            # Dividir em grupos de 8 bits
            octets = [ip_bits[i:i+8] for i in range(0, 32, 8)]

            # Converter cada grupo de bits para decimal
            octets_decimal = [int(octet, 2) for octet in octets]

            # Formatar no estilo "xxx.xxx.xxx.xxx"
            destination = ".".join(map(str, octets_decimal))

            if is_server:
                device_logger.info(f"RECEIVED TASK SEQ={fields[2]} LENGTH={len(message)} ID={fields[3]} TASK_TYPE=IPERF IP={destination} FREQUENCY={fields[5]} THRESHOLD=[BANDWIDTH:{fields[6][0]}Mbps, JITTER:{fields[6][1]}ms, LOSS: {fields[6][2]}%]")
            else:
                device_logger.info(f"RECEIVED TASK SEQ={fields[2]} LENGTH={len(message)} ID={fields[3]} TASK_TYPE=IPERF DESTINATION={destination} FREQUENCY={fields[5]} THRESHOLD=[BANDWIDTH:{fields[6][0]}Mbps, JITTER:{fields[6][1]}ms, LOSS: {fields[6][2]}%]")
            fields.append(destination)
                
        # Task_type == 4 -> Interfaces 
        elif fields[4] == 4:
            
            # Divide em blocos de 8 bit
            chunks = [bits[56:136][i:i+8] for i in range(0, 80, 8)]

            # Converte cada bloco de 8 bits num char
            original_string = ''.join(chr(int(chunk, 2)) for chunk in chunks)

            # Remove possíveis espaços adicionais adicionados por ljust ou rjust
            original_string = original_string.strip()
            fields.append(original_string)
            
            device_logger.info(f"RECEIVED TASK SEQ={fields[2]} LENGTH={len(message)} ID={fields[3]} TASK_TYPE=INTERFACE INTERFACE={original_string} FREQUENCY={fields[5]}")

    # Se for uma Metric
    elif fields[1] == Message_type.METRIC.value:
        task_id = int(bits[24:29], 2)
        task_type = int(bits[29:32], 2)

        # CPU, RAM, latência e interfaces -> apenas 1 valor
        if task_type == 0: 
            metric = int(bits[32:48], 2)  
            device_logger[fields[0]].info(f"RECEIVED CPU METRIC from AGENT{fields[0]} SEQ={fields[2]} LENGTH={len(message)} TASK_ID={task_id} METRIC={metric}%")
        # Throughput (inclui Largura de banda, jitter e perdas) -> 4 valores
        elif task_type == 1: 
            metric = int(bits[32:48], 2)  
            device_logger[fields[0]].info(f"RECEIVED RAM METRIC from AGENT{fields[0]} SEQ={fields[2]} LENGTH={len(message)} TASK_ID={task_id} METRIC={metric}%")
        elif task_type == 2: 
            metric = int(bits[32:48], 2)  
            device_logger[fields[0]].info(f"RECEIVED LATENCY METRIC from AGENT{fields[0]} SEQ={fields[2]} LENGTH={len(message)} TASK_ID={task_id} METRIC={metric}ms")
        elif task_type == 4: 
            metric = int(bits[32:48], 2)  
            device_logger[fields[0]].info(f"RECEIVED INTERFACE METRIC from AGENT{fields[0]} SEQ={fields[2]} LENGTH={len(message)} TASK_ID={task_id} METRIC=UP")
        else:  
            metric = list() 
            metric.append(int(bits[32:48],2))
            metric.append(chr(int(bits[48:56], 2)))
            metric.append(int(bits[56:72],2))
            metric.append(int(bits[72:80],2))
            device_logger[fields[0]].info(f"RECEIVED IPERF METRIC from AGENT{fields[0]} SEQ={fields[2]} LENGTH={len(message)} TASK_ID={task_id} METRIC={metric[0]}{metric[1]}bps, {metric[2]}ms, {metric[3]}%")
          
        fields.append(task_id) 
        fields.append(task_type) 
        fields.append(metric)

    # Se for um End
    elif fields[1] == Message_type.END.value:
        if server:
            device_logger[fields[0]].info(f"RECEIVED END PACKET from AGENT{fields[0]}")
        else:    
            device_logger.info(f"RECEIVED END PACKET from SERVER")
        # TODO
    
    return fields 

# Carrega tarefas atribuídas a um agente a partir de um ficheiro JSON.
def parse_tasks(agent_name : str) -> dict:
    data : dict = dict()
    
    with open("agent" + agent_name + ".json", "r") as file_json: # with garante que há um close do open
            data = json.load(file_json)
    
    # Dicionário com as tarefas do agente
    return data
