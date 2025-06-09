import { useState } from "react";
import { initializeApp } from "firebase/app";
import {
  getFirestore,
  collection,
  doc,
  addDoc,
  setDoc,
  getDocs,
  getDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  serverTimestamp,
} from "firebase/firestore";

const firebaseConfig = {
    apiKey: document.getElementById("saro").getAttribute("db-key"),
    authDomain: "isalgo-91bf7.firebaseapp.com",
    projectId: "isalgo-91bf7",
    storageBucket: "isalgo-91bf7.firebasestorage.app",
    messagingSenderId: "1087283074977",
    appId: "1:1087283074977:web:878e1a02f29429bf30dde0"
  };
document.getElementById("saro").removeAttribute("db-key");

const app = initializeApp(firebaseConfig);
const db = getFirestore();

export function useFirebaseChat() {
  const [chats, setChats] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 🟢 Get all chats for a specific user
  const getChatsByUser = async (userId) => {
    setLoading(true);
    try {
      const q = query(
        collection(db, "chats"),
        where("userId", "==", userId),
        orderBy("updatedAt", "desc") // Most recent chats first
      );
      const querySnapshot = await getDocs(q);
      const chatsList = querySnapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data(),
      }));
    //   console.log(chatsList)
      setChats(chatsList);
      return chatsList;
    } catch (err) {
      console.error("Error fetching chats:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // 🟢 Get all messages of a specific chat
  const getMessagesByChat = async (chatId) => {
    setLoading(true);
    try {
      const messagesRef = collection(db, "chats", chatId, "messages");
      const q = query(messagesRef, orderBy("createdAt", "asc"));
      const querySnapshot = await getDocs(q);
      const messagesList = querySnapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data(),
      }));

      setChats(prev => prev.map(chat => chat.id === chatId ? {...chat, messages: messagesList} : chat))
      setMessages(messagesList);
      return messagesList;
    } catch (err) {
      console.error("Error fetching messages:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // 🟢 Create a new chat
  const createChat = async (userId, title, message, answer) => {
    setLoading(true);
    try {
      // Create chat document
      const newChatRef = await addDoc(collection(db, "chats"), {
        title,
        userId: userId.toString(),
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      });

      const chatId = newChatRef.id;

      await sendMessage(chatId, message, answer);
      

      return chatId; // Return chat ID after creation
    } catch (err) {
      console.error("Error creating chat:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // 🟢 Send a message to a chat
  const sendMessage = async (chatId, question, answer) => {
    setLoading(true);
    try {
      // Add message to Firestore
      await addDoc(collection(db, "chats", chatId, "messages"), {
        question,
        answer,
        createdAt: serverTimestamp(),
      });

      // Update chat's `updatedAt` field
      const chatRef = doc(db, "chats", chatId);
      await setDoc(chatRef, { updatedAt: serverTimestamp() }, { merge: true });
    } catch (err) {
      console.error("Error sending message:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // 🟢 Delete a chat and all its messages
  const deleteChat = async (chatId) => {
    setLoading(true);
    try {
      // Delete all messages in the chat
      const messagesRef = collection(db, "chats", chatId, "messages");
      const messagesSnapshot = await getDocs(messagesRef);

      const deletePromises = messagesSnapshot.docs.map((msg) =>
        deleteDoc(doc(db, "chats", chatId, "messages", msg.id))
      );

      await Promise.all(deletePromises);

      // Delete the chat itself
      await deleteDoc(doc(db, "chats", chatId));
    } catch (err) {
      console.error("Error deleting chat:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return {
    chats,
    messages,
    loading,
    error,
    getChatsByUser,
    getMessagesByChat,
    createChat,
    sendMessage,
    deleteChat,
  };
}