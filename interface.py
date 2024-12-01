import tkinter as tk
from tkinter import messagebox

def add_log(text_widget, log_message):
    text_widget.insert(tk.END, log_message + "\n")
    text_widget.yview(tk.END)

def update_server_info():
    ip = ip_entry.get()
    port = port_entry.get()
    status = "Ativo" if ip and port else "Inativo"
    
    ip_label.config(text=f"IP: {ip}")
    port_label.config(text=f"Porta: {port}")
    status_label.config(text=f"Estado: {status}")
    
    add_log(server_log_text, f"Servidor iniciado em {ip}:{port} com estado {status}")

def search_agent():
    agent_id = agent_entry.get()
    if agent_id:
        add_log(agent_log_text, f"o agente com ID: {agent_id}")
    else:
        messagebox.showerror("Erro", "insira um ID de agente para pesquisar.")

root = tk.Tk()
root.title("NMS - Network Management System")

frame_server = tk.Frame(root, padx=10, pady=10, relief="solid", borderwidth=2)
frame_server.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

frame_agent = tk.Frame(root, padx=10, pady=10, relief="solid", borderwidth=2)
frame_agent.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

server_label = tk.Label(frame_server, text="Painel do Servidor", font=("Helvetica", 14))
server_label.pack(pady=10)

ip_label = tk.Label(frame_server, text="IP: Não Conectado", font=("Helvetica", 12))
ip_label.pack()

port_label = tk.Label(frame_server, text="Porta: Não Conectado", font=("Helvetica", 12))
port_label.pack()

status_label = tk.Label(frame_server, text="Estado: Inativo", font=("Helvetica", 12))
status_label.pack()

ip_entry = tk.Entry(frame_server, width=30)
ip_entry.insert(0, "127.0.0.1")
ip_entry.pack(pady=5)

port_entry = tk.Entry(frame_server, width=30)
port_entry.insert(0, "8080")
port_entry.pack(pady=5)

update_server_button = tk.Button(frame_server, text="Atualizar Informação", command=update_server_info)
update_server_button.pack(pady=10)

server_log_label = tk.Label(frame_server, text="Logs do Servidor:", font=("Helvetica", 12))
server_log_label.pack()

server_log_text = tk.Text(frame_server, width=70, height=25)
server_log_text.pack(pady=10)

agent_label = tk.Label(frame_agent, text="Painel do Agente", font=("Helvetica", 14))
agent_label.pack(pady=10)

agent_label_search = tk.Label(frame_agent, text="Agente a Consultar:")
agent_label_search.pack()

agent_entry = tk.Entry(frame_agent, width=30)
agent_entry.pack(pady=5)

search_agent_button = tk.Button(frame_agent, text="Pesquisar Agente", command=search_agent)
search_agent_button.pack(pady=10)

agent_log_label = tk.Label(frame_agent, text="Logs do Agente:", font=("Helvetica", 12))
agent_log_label.pack()

agent_log_text = tk.Text(frame_agent, width=70, height=30)
agent_log_text.pack(pady=10)

root.mainloop()