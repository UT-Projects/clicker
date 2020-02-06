from clicker import app

app.secret_key = 'mysecret'
app.run(host='0.0.0.0', port=80, debug=True)