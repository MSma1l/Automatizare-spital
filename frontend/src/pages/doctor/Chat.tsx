import React, { useEffect, useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../../services/api';
import { getSocket } from '../../services/socket';
import { useAuth } from '../../contexts/AuthContext';
import { Send, Paperclip, Video, Phone } from 'lucide-react';

const DoctorChat: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConvo, setActiveConvo] = useState<number | null>(location.state?.conversationId || null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get('/chat/conversations').then(res => setConversations(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (activeConvo) {
      api.get(`/chat/conversations/${activeConvo}/messages`)
        .then(res => setMessages(res.data))
        .catch(() => {});
    }
  }, [activeConvo]);

  useEffect(() => {
    const socket = getSocket();
    if (socket) {
      const handler = (msg: any) => {
        if (msg.conversation_id === activeConvo) {
          setMessages(prev => [...prev, msg]);
        }
        // Update conversation list
        setConversations(prev => prev.map(c =>
          c.id === msg.conversation_id ? { ...c, last_message: msg.content, updated_at: msg.created_at } : c
        ));
      };
      socket.on('new_message', handler);
      return () => { socket.off('new_message', handler); };
    }
  }, [activeConvo]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (!newMessage.trim() || !activeConvo) return;
    const socket = getSocket();
    if (socket) {
      socket.emit('send_message', { conversation_id: activeConvo, content: newMessage });
      setNewMessage('');
    }
  };

  const uploadFile = async (file: File) => {
    if (!activeConvo) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post(`/chat/conversations/${activeConvo}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessages(prev => [...prev, res.data]);
    } catch {
      // handle error silently
    }
  };

  const activeConversation = conversations.find(c => c.id === activeConvo);

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Conversation list */}
      <div className="w-80 border-r border-gray-100 flex flex-col">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">Conversații</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.map(c => (
            <div
              key={c.id}
              onClick={() => setActiveConvo(c.id)}
              className={`p-4 border-b border-gray-50 cursor-pointer hover:bg-gray-50 ${activeConvo === c.id ? 'bg-primary-50' : ''}`}
            >
              <div className="flex items-center justify-between">
                <p className="font-medium text-gray-800 text-sm">{c.patient_name}</p>
                {c.unread_count > 0 && (
                  <span className="w-5 h-5 bg-primary-500 text-white text-xs rounded-full flex items-center justify-center">{c.unread_count}</span>
                )}
              </div>
              {c.last_message && <p className="text-xs text-gray-400 mt-1 truncate">{c.last_message}</p>}
            </div>
          ))}
          {conversations.length === 0 && <p className="text-center text-gray-400 text-sm p-4">Nicio conversație</p>}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {activeConvo ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-800">{activeConversation?.patient_name}</p>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 text-gray-400 hover:text-primary-500 rounded-lg" title="Apel video">
                  <Video size={20} />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map(m => (
                <div key={m.id} className={`flex ${m.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                    m.sender_id === user?.id
                      ? 'bg-primary-500 text-white rounded-br-md'
                      : 'bg-gray-100 text-gray-800 rounded-bl-md'
                  }`}>
                    {m.content && <p className="text-sm">{m.content}</p>}
                    {m.file_url && (
                      m.file_type === 'image'
                        ? <img src={m.file_url} alt="" className="max-w-full rounded-lg mt-1" />
                        : <a href={m.file_url} target="_blank" rel="noreferrer" className="text-sm underline">Descarcă fișier</a>
                    )}
                    <p className={`text-xs mt-1 ${m.sender_id === user?.id ? 'text-primary-200' : 'text-gray-400'}`}>
                      {new Date(m.created_at).toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-100">
              <div className="flex items-center gap-2">
                <button onClick={() => fileInputRef.current?.click()} className="p-2 text-gray-400 hover:text-primary-500">
                  <Paperclip size={20} />
                </button>
                <input ref={fileInputRef} type="file" className="hidden" onChange={e => {
                  if (e.target.files?.[0]) uploadFile(e.target.files[0]);
                }} />
                <input
                  type="text"
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  placeholder="Scrieți un mesaj..."
                  className="flex-1 px-4 py-2 border border-gray-200 rounded-full focus:ring-2 focus:ring-primary-500 outline-none"
                />
                <button onClick={sendMessage} className="p-2 bg-primary-500 text-white rounded-full hover:bg-primary-600">
                  <Send size={18} />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            Selectați o conversație
          </div>
        )}
      </div>
    </div>
  );
};

export default DoctorChat;
