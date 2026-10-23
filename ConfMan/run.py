from cms_app import create_app

# AUTO_SEED loads the demo data the first time the app starts with an empty database.
app = create_app({"AUTO_SEED": True})

if __name__ == "__main__":
    app.run(debug=False, port=5000)
