# 📖 Story Generation API

An AI-powered API for generating **children’s stories with illustrations**.
Built using **FastAPI**, integrated with the **ChatGPT API** for text generation and **Image APIs** for illustrations.

The API allows users to specify:

* **Title**
* **Prompt / Idea**
* **Age group**
* **Language**
* **Style**
* **Number of sections (pages)**

Each section returns **story text + an image prompt**.

---

## 🚀 Features

* **Story Generation**

  * Generates a story with multiple sections.
  * Customizable by **age group**, **style**, and **language**.

* **Image Generation**

  * Each section comes with an **image prompt**.
  * Can generate illustrations via **DALL·E / Stable Diffusion API**.

* **FastAPI Backend**

  * REST API endpoints.
  * JSON-based responses.

* **Environment Config with dotenv**

  * Keeps API keys safe and out of source code.

---

## 📂 Project Structure

```
story-api/
│── core/
│   ├── story_core.py         # Core logic: generate_story & generate_image
│── api/
│   ├── routes.py             # FastAPI routes
│── main.py                   # Entry point for FastAPI app
│── requirements.txt          # Python dependencies
│── .env                      # Environment variables (not committed)
│── README.md                 # Project documentation
```

---

## ⚙️ Installation

### 1. Clone Repo

```bash
git clone https://github.com/yourusername/story-api.git
cd story-api
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Setup

Create a **`.env`** file in the project root:

```ini
OPENAI_API_KEY=your_openai_api_key_here
IMAGE_API_KEY=your_image_api_key_here
```

The app uses **python-dotenv** to load these variables.

---

## ▶️ Running the API

Start the server with:

```bash
uvicorn main:app --reload
```

Visit:
👉 `http://127.0.0.1:8000/docs` for **Swagger UI**
👉 `http://127.0.0.1:8000/redoc` for **ReDoc API docs**

---

## 📡 API Endpoints

### 1. Generate Story

**POST** `/story`

#### Request body:

```json
{
  "title": "The Brave Little Fox",
  "prompt": "A fox goes on an adventure in the forest",
  "age": 6,
  "language": "English",
  "style": "Rhyming, lyrical",
  "sections": 5
}
```

#### Response:

```json
{
  "title": "The Brave Little Fox",
  "sections": [
    {
      "id": 1,
      "text": "Once upon a time, a fox went deep into the forest...",
      "image_prompt": "A cute fox in a forest, children’s book illustration"
    },
    {
      "id": 2,
      "text": "The fox met a wise owl who showed him the way...",
      "image_prompt": "Friendly owl talking to fox, colorful kids book style"
    }
  ]
}
```

---

### 2. Generate Image

**POST** `/image`

#### Request body:

```json
{
  "image_prompt": "A friendly fox in a magical forest",
  "size": "1024x1024"
}
```

#### Response:

```json
{
  "image_url": "https://cdn.openai.com/image123.png"
}
```

---

## 🛠️ Implementation Details

* **Story Generation**

  * Uses ChatGPT API (`gpt-4o-mini` or `gpt-4.1`) to generate structured story sections.
  * Each section includes both **text** and an **image prompt**.

* **Image Generation**

  * Default: OpenAI DALL·E.
  * Extensible: can plug in Stable Diffusion API.

* **FastAPI**

  * Lightweight & async.
  * Auto-generated API docs with Swagger.

---

## 🧪 Example cURL

```bash
curl -X POST "http://127.0.0.1:8000/story" \
-H "Content-Type: application/json" \
-d '{
  "title": "Sparkle Tooth",
  "prompt": "A fun story about brushing teeth",
  "age": 5,
  "language": "English",
  "style": "Playful, rhyming",
  "sections": 3
}'
```

---

## 📦 Deployment

### Docker

1. Build image:

```bash
docker build -t story-api .
```

2. Run container:

```bash
docker run -p 8000:8000 story-api
```

---

## ✅ To-Do / Future Improvements

* [ ] Add authentication (API key-based).
* [ ] Add user profiles & story history.
* [ ] Export stories to **PDF/EPUB**.
* [ ] Multi-language TTS (read the story aloud).
* [ ] Web frontend for kids to interact with stories.

---

## 👩‍💻 Contributors

* **You** – Project lead & developer
* (Add collaborators here)

---

Would you like me to also create a **matching `requirements.txt`** (with FastAPI, requests, python-dotenv, openai, etc.) so you can run this instantly?
