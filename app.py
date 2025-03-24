from flask import Flask, render_template

app = Flask(__name__)

# Mock data
products = [
    {
        "id": 1,
        "name": "Item 1",
        "description": "Lorem ipsum dolor sit amet, consectetur.",
        "price": 49.99,
        "image_url": "https://us.karhu.com/cdn/shop/products/Photo_1_c2c9d1a3-bcb1-49fd-bf9a-79542dddf04d_1500x.jpg?v=1649252687",
        "seller": "user123",
    },
    {
        "id": 2,
        "name": "Item 2",
        "description": "Pellentesque facilisis velit vel magna rhoncus.",
        "price": 99.99,
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMAV0SMs60nMmL82cshC31Szx47zY2orrZ_g&s",
        "seller": "user456",
    },
    {
        "id": 3,
        "name": "Item 3",
        "description": "Quisque pretium ipsum sit amet risus.",
        "price": 19.99,
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvCGnx81CVQwVRZhYk2cG1l877r9aalHyw4A&s",
        "seller": "user789",
    },
        {
        "id": 4,
        "name": "Item 4",
        "description": "Mauris euismod purus et nulla pretium lobortis.",
        "price": 39.99,
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLyhOLffs7flQfwAFzPjGvwe-2RZzKefyrZA&s",
        "seller": "user111",
    },
]

@app.route('/')
def home():
    return render_template('index.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)