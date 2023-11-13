const { Schema, model } = require("mongoose");

const CarLogs = new Schema(
  {
    car_Full_NumberPlate: { type: String, required: false, unique: false },
    car_type: { type: String, required: false, unique: false },
    integrated_Payment_gateway: { type: String, required: false, unique: false },
    paymentStatus: { type: String, required: false, unique: false },
  },
  { timestamps: true }
);

CarLogs.index({ car_Full_NumberPlate: 1 });

const Logs = model("Logs", CarLogs);

module.exports = Logs;