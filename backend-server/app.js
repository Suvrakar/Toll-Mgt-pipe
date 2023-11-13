const express = require("express");
const bodyParser = require("body-parser");
const jwt = require("jsonwebtoken");
const cors = require("cors");
const _ = require("lodash");
const mongoose = require("mongoose");
require("dotenv").config();
const Logs = require("./models/carLogs");

const app = express();
app.use(express.json());
app.use(cors());
const port = 3000;

const clients = [];

function sendSSEUpdate(data) {
  const eventData = `data: ${JSON.stringify(data)}\n\n`;

  // Iterate through connected clients and send the update
  // (Assuming you have a list of connected clients)
  // Example: clients.forEach(client => client.write(eventData));
  clients.forEach((client) => {
    client.write(eventData);
  });
}

// Replace this array with your actual user data
const users = [
  {
    id: 1,
    name: "suvra",
    email: "kar.suvra@gmail.com",
    password: "12346",
  },
];

mongoose
  .connect(process.env.DB_URL, {
    useNewUrlParser: true,
  })
  .then(() => {
    console.log("Connected to MongoDB");
  })
  .catch((error) => {
    console.error("Error connecting to MongoDB:", error);
  });

const jwtOptions = {};
jwtOptions.secretOrKey = process.env.JWT_SECRET || "secret";

const requireAuth = (req, res, next) => {
  const token = req.headers.authorization;
  if (!token) {
    return res.status(401).json({ message: "Unauthorized: Missing token" });
  }

  jwt.verify(token, jwtOptions.secretOrKey, (err, decoded) => {
    if (err) {
      return res.status(401).json({ message: "Unauthorized: Invalid token" });
    }

    const user = users.find((u) => u.id === decoded.id);
    if (!user) {
      return res.status(401).json({ message: "Unauthorized: User not found" });
    }

    req.user = user;
    next();
  });
};

app.use(bodyParser.json());

// Login endpoint
app.post("/login", function (req, res) {
  if (req.body.email && req.body.password) {
    var email = req.body.email;
    var password = req.body.password;
  }
  var user = users[_.findIndex(users, { email: email })];
  if (!user) {
    res.status(401).json({ message: "No such user/email id found" });
  }

  if (user.password === password) {
    var payload = { id: user.id };
    var token = jwt.sign(payload, jwtOptions.secretOrKey);
    res.json({ message: "Successful", data: { token: token } });
  } else {
    res.status(401).json({ message: "Passwords did not match" });
  }
});

app.post("/api/process_ocr", async (req, res) => {
  const { text } = req.body;
  const { car_type, integrated_Payment_gateway, paymentStatus } = req.body;

  const newLog = new Logs({
    car_type,
    integrated_Payment_gateway,
    paymentStatus,
    car_Full_NumberPlate: text,
  });

  try {
    const savedLog = await newLog.save();

    console.log("Received OCR Result and saved to database:", savedLog);

    res.json({ status: "OCR result received and saved successfully" });
  } catch (error) {
    console.error("Error saving OCR result to database:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.get("/api/process_ocr", async (req, res) => {
  try {
    const logs = await Logs.find({});
    res.json({ carLogs: logs });
  } catch (error) {
    console.error("Error retrieving carLogs:", error);
    res.status(500).json({ message: "Failed to retrieve carLogs" });
  }
});


app.listen(port, () => {
  console.log(`Express server listening at http://localhost:${port}`);
});
