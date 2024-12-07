from flask import Flask, render_template, jsonify
import logging

def web_app(address, agents_data):
    app = Flask(__name__)
    log = logging.getLogger('werkzeug')
    log.disabled = True
    @app.context_processor
    def inject_global_data():
    # Make agents_data available globally in templates
        return {"agents_data": agents_data}

    @app.route('/sidebar')
    def get_sidebar_data():
        """Serve JSON data for the sidebar."""
        return jsonify(list(agents_data.keys()))

    @app.route('/')
    def index():
        return render_template('index.html', agents=list(agents_data.keys()))

    @app.route('/<agent_name>')
    def agent_page(agent_name):
        if agent_name in agents_data:
            return render_template('agent_page.html', agent_name=agent_name)
        return render_template('404.html', title="Agent Not Found"), 404

    @app.route('/data/<agent_name>')
    def get_agent_data(agent_name):
        """Serve JSON data for a specific agent."""
        
        if agent_name != "favicon.ico" and agent_name in agents_data:
            return jsonify(agents_data[agent_name].get_metrics())
        return jsonify({"error": "Agent not found"}), 404

    @app.route('/agents')
    def get_agents():
        """Serve the list of agents."""
        return jsonify(list(agents_data.keys()))

    #app.run(host=address, port=5001, debug=True)
    app.run(host='0.0.0.0',debug=False)