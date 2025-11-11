import asyncio
import logging
import os
import sys
import json
from queue import Queue
import markdown
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
    make_response,
)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import root_agent
from agentmain.runner import RestaurantRunner

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Logging Setup for SSE ---
log_queue = Queue()

class QueueHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        self.queue.put(record)

# Get the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Create a handler that writes to the queue
queue_handler = QueueHandler(log_queue)
# No formatter needed here, formatting will happen in the generator

# Add the handler to the root logger
root_logger.addHandler(queue_handler)


@app.route('/stream-logs')
def stream_logs():
    def generate():
        # Create a formatter for the log messages
        formatter = logging.Formatter('%(asctime)s')
        while True:
            record = log_queue.get()  # This will block until a message is available
            log_entry = {
                'timestamp': formatter.formatTime(record, "%Y-%m-%d %H:%M:%S"),
                'name': record.name,
                'levelname': record.levelname,
                'message': record.getMessage()
            }
            yield f"data: {json.dumps(log_entry)}\n\n"
    return Response(generate(), mimetype='text/event-stream')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('chat'))
    return render_template('index.html')


@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'])


@app.route('/ask', methods=['POST'])
def ask():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    username = session['username']
    agent_session_id = request.cookies.get('agent_session_id')

    try:
        # Instantiate the runner for each request to capture the session
        runner = RestaurantRunner(
            agent=root_agent,
            user_id=username,
            session_id=agent_session_id
        )

        # Run the agent
        agent_response_md = asyncio.run(runner.call_agent(user_message))

        # Convert markdown response to HTML
        agent_response_html = markdown.markdown(agent_response_md or "No response from agent.")

        # Create the response
        response_data = {
            'agent_response': agent_response_html,
        }
        
        # Create a response object to set the cookie
        resp = make_response(jsonify(response_data))
        
        # Update the session ID cookie
        if runner._session_id:
            resp.set_cookie('agent_session_id', runner._session_id)
            
        return resp

    except Exception as e:
        logging.error(f"Error calling agent: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8080)