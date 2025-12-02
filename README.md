```markdown
# Production Planning Dashboard — Implementation Summary

This project delivers a fully working **Production Planning Dashboard** with:

- **FastAPI backend**
- **MongoDB database**
- **React frontend**
- **AI-powered Excel parsing (OpenAI GPT-4o-mini)**
- **Fallback heuristic parsing**
- **Real-time production metrics**
- **Database reset functionality**

The system parses messy Excel files from different vendors (e.g., Adidas, Under Armour, Nike), cleans and normalizes the data, stores it in MongoDB, and visualizes the production pipeline in a clean dashboard UI.

---

## ✅ Features Implemented

### **1. AI-Enhanced Excel Parsing**
- GPT-4o-mini maps messy Excel column names → canonical fields.
- GPT extracts:
  - Order Number  
  - Style  
  - Fabric  
  - Color  
  - Quantity  
  - Timeline stages (Cutting, Feeding, VAP, Shipping, etc.)  
- Works safely inside a timeout using a fallback parser.

### **2. Fallback Heuristic Parser**
When GPT is unavailable or fails:
- Normalize column names (`lowercase`, underscores)
- Auto-detect fields using heuristics
- Extract dates, quantities, and raw context
- Generate `in_production`, `pending`, or `completed` statuses

### **3. Strict Filtering Logic**
Only valid, meaningful rows are saved:
- Must have **valid order_number**
- Must have **valid numeric quantity**
- Must not contain `"None"`, `"nan"`, `"null"` etc.
- Prevents junk items from polluting DB

### **4. MongoDB Async Integration**
- `AsyncIOMotorClient` for fully async operations  
- Collection: `production.items`
- JSON-safe cleaning for:
  - ObjectId  
  - NaN / Infinity  
  - Nested floats  

### **5. Clean API Layer**
#### Endpoints:
- `GET /api/production-items`  
- `POST /api/upload`  
- `POST /api/reset-db`  
- `GET /health`

All responses are sanitized for frontend safety.

### **6. React Frontend**
Built a clean, functional production dashboard:

#### **Production Overview Widgets**
- Total Orders  
- Pending  
- In Production  
- Completed  
- Total Quantity  

Auto-updates on file upload and database reset.

#### **Production Line Cards**
Each card shows:
- Order number
- Style
- Fabric
- Color
- Quantity
- Status badge
- Timeline (with auto date formatting)
- “View Details” CTA

### **7. FileUploader Component**
- File selection UI
- Upload with progress
- Error handling
- Refreshes dashboard automatically

### **8. Reset Database**
- Fully implemented backend endpoint  
- Connected to frontend “Reset DB” button  
- Clears Mongo collection and refreshes UI instantly  

---

## 📸 Screenshots (Outputs)

### **1. Adidas File Output**
![Screenshot](./images/Screenshot%202025-12-03%20at%2012.31.07 AM.png)

### **2. Under Armour File Output**
![Screenshot](./images/Screenshot%202025-12-03%20at%2012.32.39 AM.png)

### **3. Nike File Output**
![Screenshot](./images/Screenshot%202025-12-03%20at%2012.34.42 AM.png)

If local paths are not used, here are the raw uploaded versions:

- Adidas:  
  `/mnt/data/Screenshot 2025-12-03 at 12.31.07 AM.png`
- Under Armour:  
  `/mnt/data/Screenshot 2025-12-03 at 12.32.39 AM.png`
- Nike:  
  `/mnt/data/Screenshot 2025-12-03 at 12.34.42 AM.png`

---

## 🧩 Architecture

```
backend/
  main.py → FastAPI app + AI parsing + DB logic

frontend/
  App.js → global state, upload, reset, fetch logic
  components/
    FileUploader.js → file upload handler
    ProductionCard.js
    ProductionDashboard.js
```

---

## 🚀 How to Run

### **Backend**
```bash
cd backend
uvicorn main:app --reload
```

### **Frontend**
```bash
cd frontend
npm install
npm start
```

### **Docker Compose**
```bash
docker-compose up --build
```

---

## 🎯 Requirements Fulfilled

✔ AI-powered parsing using provided OpenAI API key  
✔ Fallback logic without AI dependency  
✔ Strict data filtering  
✔ Real-time production metrics  
✔ Clean UI with cards and widgets  
✔ Excel upload and parsing  
✔ Complete MongoDB persistence  
✔ Reset database workflow  
✔ Error-free frontend build  
✔ Fully working dashboard across all three datasets  

---

## 📋 Tech Stack

**Backend:**
- FastAPI
- Motor (AsyncIO MongoDB driver)
- OpenAI GPT-4o-mini
- Pandas
- Python 3.9+

**Frontend:**
- React
- Axios
- CSS3

**Database:**
- MongoDB

**Infrastructure:**
- Docker & Docker Compose

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the backend directory:

```env
MONGODB_URL=mongodb://localhost:27017
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 📝 API Documentation

### **GET /api/production-items**
Retrieve all production items from database.

**Response:**
```json
[
  {
    "order_number": "12345",
    "style": "T-Shirt",
    "fabric": "Cotton",
    "color": "Blue",
    "quantity": 500,
    "status": "in_production",
    "timeline": { ... }
  }
]
```

### **POST /api/upload**
Upload Excel file for parsing.

**Request:** Multipart form data with file

**Response:**
```json
{
  "message": "File processed successfully",
  "items_saved": 42
}
```

### **POST /api/reset-db**
Clear all items from database.

**Response:**
```json
{
  "message": "Database reset successfully",
  "deleted_count": 42
}
```

### **GET /health**
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

## 🐛 Troubleshooting

### **MongoDB Connection Issues**
Ensure MongoDB is running:
```bash
mongod --dbpath /path/to/data
```

### **OpenAI API Errors**
Check API key validity and quota limits.

### **Frontend CORS Issues**
Backend has CORS enabled for `http://localhost:3000` by default.

---

## 📄 License

MIT License

---

## 👥 Contributors

- Sk Tausif Rahman

---

## 🚧 Future Enhancements

- [ ] Add user authentication
- [ ] Export to PDF/Excel reports
- [ ] Real-time WebSocket updates
- [ ] Advanced filtering and search
- [ ] Production timeline Gantt charts
- [ ] Email notifications for critical updates

---

For questions or support:
- Email: tausifrahman1998@yahoo.in
- GitHub: [@Tausif1998GitHub](https://github.com/Tausif1998GitHub)
- LinkedIn: [Sk Tausif Rahman](https://linkedin.com/in/tausif-rahman)
```
