from flask import Flask, jsonify
from werkzeug.exceptions import NotFound

# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>EB Flask Test</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Thelonious</code>) to say hello to
    someone specific.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'


# EB looks for an 'application' callable by default. See
# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-container.html#python-namespaces
application = Flask(__name__)

# add a rule for the index page. This is the only valid page
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username
application.add_url_rule('/', 'index', (lambda: header_text +
    say_hello() + instructions + footer_text))


# ELB will attempt to contact `/health` on the instances. See
# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/command-options-general.html#command-options-general-elbhealthcheck
def health_check():
    return jsonify({"status": "healthy"}), 200
application.add_url_rule('/health', 'health_check', health_check, methods=['GET'])


if __name__ == "__main__":
    application.debug = True
    application.run()
