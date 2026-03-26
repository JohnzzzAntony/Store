// Firebase Configuration Integration for Saleel Parfums
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, onAuthStateChanged, signOut, GoogleAuthProvider, signInWithPopup, signInAnonymously } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getFirestore, doc, setDoc, getDoc, collection, serverTimestamp, onSnapshot, query, orderBy, limit } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

// Placeholder for User's Firebase Config
// The user should replace this with their actual project configuration from the Firebase Console
const firebaseConfig = {
  apiKey: "AIzaSyAm2MuyUUzt0SN9TE6JKn7kBqu-gzzJPow",
  authDomain: "store-c7c7a.firebaseapp.com",
  projectId: "store-c7c7a",
  storageBucket: "store-c7c7a.firebasestorage.app",
  messagingSenderId: "313991721235",
  appId: "1:313991721235:web:ce4e15eef757cd0e15aae6",
  measurementId: "G-94DE173MN0"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

export { auth, db, signInWithEmailAndPassword, createUserWithEmailAndPassword, onAuthStateChanged, signOut, doc, setDoc, getDoc, collection, serverTimestamp, GoogleAuthProvider, signInWithPopup, onSnapshot, query, orderBy, limit, signInAnonymously };
