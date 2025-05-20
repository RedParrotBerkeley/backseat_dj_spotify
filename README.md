# Backseat DJ (SpotAPI Edition)

Let your passengers request music from the back seat using a simple QR code and web form. This MVP version uses **SpotAPI** to control Spotify playback without needing official API keys — perfect for personal testing.

---

## 🚗 What It Does

- Lets users submit song requests via a web form
- Maintains a simple in-memory request queue
- Uses [SpotAPI](https://github.com//guilhem/spotapi) to log into Spotify with your credentials
- Searches and plays songs automatically from the driver’s active Spotify session

---

## 🛠 Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- HTML + CSS frontend (no JS required)
- [SpotAPI](https://github.com//guilhem/spotapi) (unofficial Spotify wrapper)
- Python 3.11+

---

## 🧪 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/RedParrotBerkeley/backseat-dj.git
cd backseat-dj
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Set Your Spotify Credentials

Create a `.env` file in the root directory with the following:

```env
SPOTIFY_USERNAME=your_email
SPOTIFY_PASSWORD=your_password
```

**Important:** Never commit your `.env` file to source control. Make sure it's in your `.gitignore`.

### 4. Run the App

```bash
uvicorn main:app --reload
```

Visit:

```
http://localhost:8000
```

---

## ⚠️ Warning

This version uses unofficial access to Spotify’s private endpoints via SpotAPI.

> **Do not use this in production or with other people’s accounts.**  
> It may violate [Spotify’s Terms of Service](https://www.spotify.com/legal/end-user-agreement/).

---

## ✅ Roadmap

- [ ] Replace SpotAPI with official Spotify API (OAuth 2.0)
- [ ] Add admin dashboard
- [ ] Add device selector and playback target
- [ ] Deploy on Replit / Vercel with public QR interface
- [ ] Build Amazon Music version once API access is granted

---

## 📬 Contact
Mike Patraw  
📧 mpatraw@berkeley.edu
```
