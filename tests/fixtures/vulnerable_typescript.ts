import express from 'express';
import db from './db'; // Assuming db is imported from a local module
import User from './User'; // Assuming User is imported from a local module

// SQL Injection vulnerability
async function getUserData(userId: string) {
  const query = `SELECT * FROM users WHERE id = ${userId}`;
  return await db.query(query);
}

// IDOR (Insecure Direct Object Reference)
export async function getUserProfile(req: express.Request, res: express.Response) {
  const userId = req.params.userId;
  const profile = await User.findById(userId);
  res.json(profile);
}

// Hardcoded credentials
const dbConfig = {
  host: 'localhost',
  user: 'admin',
  password: 'password123',
  database: 'production_db'
};
