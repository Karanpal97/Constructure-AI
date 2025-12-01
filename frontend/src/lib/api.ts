const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

export interface Email {
  id: string;
  thread_id: string;
  sender: string;
  sender_email: string;
  subject: string;
  snippet: string;
  body: string;
  date: string;
  is_unread: boolean;
  labels: string[];
}

export interface EmailSummary {
  email: Email;
  summary: string;
  category?: string;
}

export interface EmailResponse {
  email_id: string;
  original_subject: string;
  original_sender: string;
  suggested_reply: string;
  tone: string;
}

export interface ChatResponse {
  message: string;
  action_type?: string;
  action_data?: Record<string, unknown>;
  emails?: EmailSummary[];
  suggested_replies?: EmailResponse[];
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("auth_token");
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }

  async getLoginUrl(): Promise<{ authorization_url: string; state: string }> {
    const response = await fetch(`${API_URL}/auth/login`);
    if (!response.ok) {
      throw new Error("Failed to get login URL");
    }
    return response.json();
  }

  async getCurrentUser(): Promise<UserProfile> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_URL}/auth/me?token=${token}`);
    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
        throw new Error("Session expired");
      }
      throw new Error("Failed to get user profile");
    }
    return response.json();
  }

  async verifyToken(): Promise<{
    valid: boolean;
    user_id?: string;
    email?: string;
    has_gmail_access?: boolean;
  }> {
    const token = this.getToken();
    if (!token) return { valid: false };

    const response = await fetch(`${API_URL}/auth/verify?token=${token}`);
    return response.json();
  }

  async logout(): Promise<void> {
    const token = this.getToken();
    if (token) {
      await fetch(`${API_URL}/auth/logout?token=${token}`, { method: "POST" });
    }
    this.clearToken();
  }

  async getWelcomeMessage(): Promise<{ message: string; user_name: string }> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_URL}/chat/welcome?token=${token}`);
    if (!response.ok) {
      throw new Error("Failed to get welcome message");
    }
    return response.json();
  }

  async sendChatMessage(message: string): Promise<ChatResponse> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_URL}/chat/message?token=${token}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
        throw new Error("Session expired");
      }
      throw new Error("Failed to send message");
    }
    return response.json();
  }

  async fetchEmails(count = 5, query?: string): Promise<EmailSummary[]> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");

    const params = new URLSearchParams({ token, count: String(count) });
    if (query) params.append("query", query);

    const response = await fetch(`${API_URL}/emails/list?${params}`);
    if (!response.ok) {
      throw new Error("Failed to fetch emails");
    }
    return response.json();
  }

  async sendEmail(emailId: string, replyContent: string): Promise<{ success: boolean; message: string }> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_URL}/emails/send?token=${token}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email_id: emailId,
        reply_content: replyContent,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to send email");
    }
    return response.json();
  }

  async deleteEmail(emailId: string, confirm = true): Promise<{ success: boolean; message: string }> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_URL}/emails/delete?token=${token}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email_id: emailId,
        confirm,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to delete email");
    }
    return response.json();
  }
}

export const api = new ApiClient();

