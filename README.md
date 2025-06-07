TODO make this a real README

backend:
source venv/bin/activate  ||  .\venv\Scripts\activate
cd backend
pip install -r requirements.txt
fastapi dev main.py
 
http://127.0.0.1:8000/docs

frontend:
cd frontend
npm install
npm run dev

http://localhost:5173/
