// Supabase Client Wrapper
// Inicializa el cliente y expone helpers de auth + conversaciones

(function () {
  const { createClient } = window.supabase;
  const { SUPABASE_URL, SUPABASE_ANON_KEY } = window.RE_CONFIG;

  const client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  window.SB = {
    client,

    // ===== AUTH =====
    async signUp(email, password, fullName) {
      return await client.auth.signUp({
        email,
        password,
        options: { data: { full_name: fullName } }
      });
    },

    async signIn(email, password) {
      return await client.auth.signInWithPassword({ email, password });
    },

    async signOut() {
      return await client.auth.signOut();
    },

    async getUser() {
      const { data: { user } } = await client.auth.getUser();
      return user;
    },

    onAuthChange(callback) {
      return client.auth.onAuthStateChange(callback);
    },

    // ===== CONVERSATIONS =====
    async listConversations() {
      const { data, error } = await client
        .from('conversations')
        .select('id, title, created_at, updated_at')
        .order('updated_at', { ascending: false });
      if (error) throw error;
      return data || [];
    },

    async createConversation(title = 'Nueva conversación') {
      const user = await this.getUser();
      if (!user) throw new Error('No autenticado');
      const { data, error } = await client
        .from('conversations')
        .insert({ user_id: user.id, title })
        .select()
        .single();
      if (error) throw error;
      return data;
    },

    async updateConversationTitle(id, title) {
      const { error } = await client
        .from('conversations')
        .update({ title })
        .eq('id', id);
      if (error) throw error;
    },

    async deleteConversation(id) {
      const { error } = await client
        .from('conversations')
        .delete()
        .eq('id', id);
      if (error) throw error;
    },

    // ===== MESSAGES =====
    async listMessages(conversationId) {
      const { data, error } = await client
        .from('messages')
        .select('id, role, content, created_at')
        .eq('conversation_id', conversationId)
        .order('created_at', { ascending: true });
      if (error) throw error;
      return data || [];
    },

    async addMessage(conversationId, role, content) {
      const { data, error } = await client
        .from('messages')
        .insert({ conversation_id: conversationId, role, content })
        .select()
        .single();
      if (error) throw error;
      return data;
    }
  };
})();
