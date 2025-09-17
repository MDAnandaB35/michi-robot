// Models Robot.js - Mongoose Robot Schema

const mongoose = require('mongoose');

const robotSchema = new mongoose.Schema(
  {
    robotId: { type: String, required: true, unique: true, index: true },
    robotName: { type: String, required: true },
    ownerUserIds: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User', index: true }],
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Robot', robotSchema, process.env.ROBOTS_COLLECTION || 'robots');


