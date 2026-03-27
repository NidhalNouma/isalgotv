import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";
import {
  getStreamAnswer,
  branchStreamAnswer,
  switchBranch as switchBranchAPI,
  likeMessage as likeMessageAPI,
  dislikeMessage as dislikeMessageAPI,
} from "../api/chat";

import { AI_MODELS } from "../constant";
import { type AIModel } from "../types/user";

import type {
  ChatSession,
  ChatMessage,
  StreamResponseMeta,
} from "../types/chat";

// Hook that manages a single chat session state and sending/streaming
export function useChatHook() {
  const { user, updateTokens, accounts } = useUser();
  const {
    chats,
    setChats,
    newChatAdded,
    newMessagesAdded,
    currentChat,
    selectChat,
  } = useChat();

  const chat: ChatSession | null =
    (chats as ChatSession[]).find(
      (c) => String(c.id) === String(currentChat),
    ) || null;

  const allMessages: ChatMessage[] = useMemo(
    () => (chat ? chat.messages || [] : []),
    [chat],
  );

  // ─── Branch navigation state ──────────────────────────────────
  // Maps parentId → active child id  (controls which sibling is displayed)
  const [activeBranches, setActiveBranches] = useState<
    Record<string, string | number>
  >({});

  // Reset branch selections when chat changes
  const prevBranchChat = useRef(currentChat);
  useEffect(() => {
    if (prevBranchChat.current !== currentChat) {
      setActiveBranches({});
      prevBranchChat.current = currentChat;
    }
  }, [currentChat]);

  // Back-fill parent_id for legacy messages that lack it (mirrors ensure_parent_chain on server)
  const normalizedMessages: ChatMessage[] = useMemo(() => {
    if (!allMessages.length) return allMessages;
    if (!allMessages.some((m) => m.parent_id != null)) return allMessages;
    return allMessages.map((m, i) => {
      if (i === 0 || m.parent_id != null) return m;
      return { ...m, parent_id: allMessages[i - 1].id as number };
    });
  }, [allMessages]);

  const treeMeta = useMemo(() => {
    const byId = new Map<string, ChatMessage>();
    const childrenOf = new Map<string, ChatMessage[]>();
    const rankById = new Map<string, number>();

    normalizedMessages.forEach((message, index) => {
      const id = String(message.id);
      byId.set(id, message);

      const createdAt = (
        message as ChatMessage & { created_at?: string | Date }
      ).created_at;
      const parsedTime = createdAt ? new Date(createdAt).getTime() : Number.NaN;
      rankById.set(id, Number.isFinite(parsedTime) ? parsedTime : index);

      const key =
        message.parent_id != null ? String(message.parent_id) : "__root__";
      const siblings = childrenOf.get(key) || [];
      siblings.push(message);
      childrenOf.set(key, siblings);
    });

    let roots = childrenOf.get("__root__") || [];
    if (!roots.length) {
      roots = normalizedMessages.filter((message) => {
        if (message.parent_id == null) return true;
        const id = String(message.id);
        const parentId = String(message.parent_id);
        if (parentId === id) return true;
        return !byId.has(parentId);
      });
    }

    const subtreeRankMemo = new Map<string, number>();
    const getSubtreeRank = (id: string): number => {
      if (subtreeRankMemo.has(id)) return subtreeRankMemo.get(id)!;

      const ownRank = rankById.get(id) ?? Number.MIN_SAFE_INTEGER;
      const children = childrenOf.get(id) || [];
      let bestRank = ownRank;
      for (const child of children) {
        bestRank = Math.max(bestRank, getSubtreeRank(String(child.id)));
      }

      subtreeRankMemo.set(id, bestRank);
      return bestRank;
    };

    const defaultBranches: Record<string, string | number> = {};
    for (const [parentId, children] of childrenOf.entries()) {
      if (parentId === "__root__" || children.length <= 1) continue;
      let bestChild = children[0];
      let bestRank = getSubtreeRank(String(bestChild.id));
      for (const child of children.slice(1)) {
        const childRank = getSubtreeRank(String(child.id));
        if (childRank >= bestRank) {
          bestChild = child;
          bestRank = childRank;
        }
      }
      defaultBranches[parentId] = bestChild.id;
    }

    let preferredRootId: string | number | null = null;
    if (roots.length) {
      let bestRoot = roots[0];
      let bestRank = getSubtreeRank(String(bestRoot.id));
      for (const root of roots.slice(1)) {
        const rootRank = getSubtreeRank(String(root.id));
        if (rootRank >= bestRank) {
          bestRoot = root;
          bestRank = rootRank;
        }
      }
      preferredRootId = bestRoot.id;
    }

    return {
      byId,
      childrenOf,
      roots,
      defaultBranches,
      preferredRootId,
    };
  }, [normalizedMessages]);

  // Resolve the tree of messages into a linear visible path
  const visibleMessages: ChatMessage[] = useMemo(() => {
    if (!normalizedMessages.length) return [];
    // If no message has a parent_id, display flat (legacy / no branches)
    if (!normalizedMessages.some((m) => m.parent_id != null))
      return normalizedMessages;
    console.log("[visibleMessages recompute]", {
      activeBranches: { ...activeBranches },
      msgCount: normalizedMessages.length,
      withParent: normalizedMessages
        .filter((m) => m.parent_id != null)
        .map((m) => ({ id: m.id, parent_id: m.parent_id })),
    });

    const { childrenOf, roots, defaultBranches, preferredRootId, byId } =
      treeMeta;
    if (!roots.length) {
      // Degenerate/cyclic graph fallback: keep previous behavior, but avoid breaking UI.
      return normalizedMessages;
    }

    const path: ChatMessage[] = [];
    let current: ChatMessage | undefined =
      preferredRootId != null
        ? byId.get(String(preferredRootId))
        : roots[roots.length - 1];

    while (current) {
      path.push(current);
      const kids = childrenOf.get(String(current.id));
      if (!kids?.length) break;
      const activeId: string | number | undefined =
        activeBranches[String(current.id)] ??
        defaultBranches[String(current.id)];
      if (kids.length > 1) {
        console.log("[tree fork] id=" + String(current.id), {
          kids: kids.map((k) => k.id),
          activeId,
          willPick:
            activeId != null
              ? (kids.find((c) => String(c.id) === String(activeId))?.id ??
                "fallback-last")
              : "default-last",
        });
      }
      current =
        activeId != null
          ? kids.find((c) => String(c.id) === String(activeId)) ||
            kids[kids.length - 1]
          : kids[kids.length - 1]; // default: latest branch
    }
    console.log("[visibleMessages]", {
      activeBranches,
      path: path.map((m) => ({ id: m.id, parent_id: m.parent_id })),
    });
    console.log(
      "[visibleMessages result]",
      path.map((m) => m.id),
    );
    return path;
  }, [normalizedMessages, activeBranches, treeMeta]);

  // Compute siblings map (parentId → sibling ids) for branch navigation UI
  const siblingsMap: Record<string, (string | number)[]> = useMemo(() => {
    if (!normalizedMessages.some((m) => m.parent_id != null)) return {};
    const map: Record<string, (string | number)[]> = {};
    for (const m of normalizedMessages) {
      if (m.parent_id == null) continue;
      const key = String(m.parent_id);
      if (!map[key]) map[key] = [];
      map[key].push(m.id);
    }
    return map;
  }, [normalizedMessages]);

  // Alias so existing code that reads `messages` still works
  let messages = visibleMessages;

  // Best-effort selected branch leaf:
  // start from the last explicit branch selection, then walk down using
  // active selections (or latest child by default) until a leaf is reached.
  const selectedBranchLeafId = useMemo(() => {
    const selected: Array<string | number> = Object.values(activeBranches);
    if (!selected.length || !normalizedMessages.length) return null;

    const { byId, childrenOf, defaultBranches } = treeMeta;

    const startId = String(selected[selected.length - 1]);
    let current: ChatMessage | undefined = byId.get(startId);
    if (!current) return null;

    const seen = new Set<string>();
    while (current) {
      const currentId: string = String(current.id);
      if (seen.has(currentId)) break;
      seen.add(currentId);

      const kids: ChatMessage[] = childrenOf.get(currentId) || [];
      if (!kids.length) break;

      const activeId: string | number | undefined =
        activeBranches[currentId] ?? defaultBranches[currentId];
      current =
        activeId != null
          ? kids.find((c: ChatMessage) => String(c.id) === String(activeId)) ||
            kids[kids.length - 1]
          : kids[kids.length - 1];
    }

    return current?.id ?? null;
  }, [normalizedMessages, activeBranches, treeMeta]);

  // Build an ordered path from an arbitrary leaf back to the closest available root
  // inside the loaded window. Used to send a branch-consistent prompt payload.
  const getPathToNode = useCallback(
    (nodeId: string | number | null | undefined): ChatMessage[] => {
      if (nodeId == null || !normalizedMessages.length) return [];

      const byId = new Map<string, ChatMessage>();
      for (const m of normalizedMessages) {
        byId.set(String(m.id), m);
      }

      const path: ChatMessage[] = [];
      const seen = new Set<string>();
      let current = byId.get(String(nodeId));

      while (current) {
        const id = String(current.id);
        if (seen.has(id)) break;
        seen.add(id);
        path.push(current);

        if (current.parent_id == null) break;
        const parent = byId.get(String(current.parent_id));
        if (!parent) break;
        current = parent;
      }

      return path.reverse();
    },
    [normalizedMessages],
  );

  function setChatMessages(
    chatId: string | number | null | undefined,
    msgs: ChatMessage[],
    error: string | null = null,
    limit = false,
    isLoading = false,
  ): void {
    const id = String(chatId) ?? "new-chat";
    setChats((prev) => {
      return prev.map((c) => {
        if (String(c.id) === id) {
          return {
            ...c,
            messages: msgs || c.messages,
            error,
            limit,
            isLoading,
          } as ChatSession;
        }
        return c as ChatSession;
      });
    });
  }

  function setTypingMessage(
    chatId: string | number | null | undefined,
    messageId: string | number,
    reply: string,
  ) {
    const id = String(chatId) ?? "new-chat";
    setChats((prev) => {
      return prev.map((c) => {
        if (String(c.id) === id) {
          return {
            ...c,
            messages: (c.messages || []).map((msg) =>
              msg.id === messageId
                ? {
                    ...msg,
                    content: reply,
                    isLoading: true,
                  }
                : msg,
            ),
          } as ChatSession;
        }
        return c as ChatSession;
      });
    });
  }

  function addTempChatMessages(chatName: string, msgs: ChatMessage[]) {
    const id = "new-chat";
    setChats([
      {
        id,
        name: chatName,
        messages: msgs,
        hidden: true,
        isLoading: true,
      } as ChatSession,
      ...(chats as ChatSession[]),
    ]);
    selectChat(id);
  }

  // --- Per-chat drafts: each chat id has its own input/files ---
  const activeId = String(currentChat ?? "new-chat");

  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [fileDrafts, setFileDrafts] = useState<Record<string, File[]>>({});

  const input = drafts[activeId] ?? "";
  const files = fileDrafts[activeId] ?? [];

  const setInput = (next: string | ((prev: string) => string)) => {
    setDrafts((prev) => {
      const prevVal = prev[activeId] ?? "";
      const nextVal =
        typeof next === "function"
          ? (next as (p: string) => string)(prevVal)
          : next;
      if (nextVal === prevVal) return prev;
      return { ...prev, [activeId]: nextVal };
    });
  };

  const setFiles = (next: File[] | ((prev: File[]) => File[])) => {
    setFileDrafts((prev) => {
      const prevVal = prev[activeId] ?? [];
      const nextVal =
        typeof next === "function"
          ? (next as (p: File[]) => File[])(prevVal)
          : next;
      return { ...prev, [activeId]: nextVal };
    });
  };

  const [model, setModel] = useState<AIModel>(AI_MODELS![0]);
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const prevChatRef = useRef(currentChat);

  // Restore selectedAccount from the last message's context when switching chats or messages load
  useEffect(() => {
    const chatChanged = prevChatRef.current !== currentChat;
    prevChatRef.current = currentChat;

    if (messages.length > 0) {
      // Only check the very last message — if it has no account, the dropdown stays empty
      const lastCtx = messages[messages.length - 1].context;
      if (lastCtx?.account) {
        const match = accounts.find((a: any) => a.id === lastCtx.account.id);
        setSelectedAccount(match ?? lastCtx.account);
        return;
      }
    }
    // Clear when switching chats or when last message has no account
    if (chatChanged) {
      setSelectedAccount(null);
    }
  }, [currentChat, messages.length]);

  useEffect(() => {
    function handleDjangoMessage(e: Event) {
      const ce = e as CustomEvent<{ message: string }>;
      // console.log("Received message:", ce.detail.message);
      handleSubmit(null, ce.detail?.message);
    }
    window.addEventListener(
      "teroMessage",
      handleDjangoMessage as EventListener,
    );
    return () => {
      window.removeEventListener(
        "teroMessage",
        handleDjangoMessage as EventListener,
      );
    };
  }, [user]);

  type Chunk = { tag: string; payload: string };

  // Extracts all *complete* chunks from the buffer.
  // Non-terminal tags (data) keep the last incomplete chunk in `remaining`
  // so it can be combined with the next network read.
  function extractCompleteChunks(buffer: string): {
    chunks: Chunk[];
    remaining: string;
  } {
    const MARKER_RE = /\n<\|([a-zA-Z]+)\|>:/g;
    const TERMINAL = new Set(["done", "error", "limit"]);

    const indices: { tag: string; start: number; end: number }[] = [];
    let m: RegExpExecArray | null;
    while ((m = MARKER_RE.exec(buffer)) !== null) {
      indices.push({
        tag: m[1].toLowerCase(),
        start: m.index,
        end: m.index + m[0].length,
      });
    }

    if (indices.length === 0) {
      // No complete marker yet — keep everything in the buffer
      return { chunks: [], remaining: buffer };
    }

    const chunks: Chunk[] = [];
    for (let i = 0; i < indices.length; i++) {
      const cur = indices[i];
      const next = indices[i + 1];

      if (next) {
        // Payload is fully bounded by the next marker
        chunks.push({
          tag: cur.tag,
          payload: buffer.slice(cur.end, next.start),
        });
      } else {
        // Last marker: terminal tags are always complete (sent as a single yield)
        if (TERMINAL.has(cur.tag)) {
          chunks.push({ tag: cur.tag, payload: buffer.slice(cur.end) });
          return { chunks, remaining: "" };
        }
        // Non-terminal (data): keep from this marker onward in case it's split
        return { chunks, remaining: buffer.slice(cur.start) };
      }
    }

    return { chunks, remaining: "" };
  }

  const sendMessage = async (
    msg: string,
    files: File[] | null,
    modelName: string,
    account: any = null,
    requestMessages?: ChatMessage[],
    parentMessageId?: string | number | null,
  ) => {
    if (!msg?.trim()) return;

    const currentChatId = currentChat || "new-chat";
    // Only set isLoading; don't overwrite messages (handleSendMessage already set them with allMessages)
    setChatMessages(currentChatId, null as any, null, false, true);

    try {
      const msgs = (requestMessages || messages).filter((m) => m.content);

      let full_reply = "";
      let rawBuffer = "";
      const loadingMsgId = messages[messages.length - 1].id;

      const context = account
        ? {
            account: {
              id: account.id,
              name: account.name,
              broker_type: account.broker_type,
            },
          }
        : null;

      const stream = (await getStreamAnswer(
        msg,
        msgs,
        files,
        modelName,
        currentChat,
        context,
        parentMessageId ?? null,
      )) as AsyncIterable<string> | any;

      for await (const rawChunk of stream as AsyncIterable<string>) {
        rawBuffer += rawChunk;

        const { chunks, remaining } = extractCompleteChunks(rawBuffer);
        rawBuffer = remaining;

        for (const ch of chunks) {
          const tag = ch.tag;
          const payload = ch.payload ?? "";

          switch (tag) {
            case "data": {
              // Accumulate and stream each token directly to the UI
              full_reply += payload;
              setTypingMessage(currentChatId!, loadingMsgId, full_reply);
              break;
            }
            case "limit": {
              // Server indicates token/usage limit reached — remove loading msg from allMessages
              setChats((prev) =>
                prev.map((c) =>
                  String(c.id) === String(currentChatId)
                    ? {
                        ...c,
                        messages: (c.messages || []).filter(
                          (m) => m.id !== loadingMsgId,
                        ),
                        limit: true,
                        isLoading: false,
                      }
                    : c,
                ),
              );
              return;
            }
            case "error": {
              // Server sent an error payload
              throw new Error(payload || "Unknown error from stream");
            }
            case "done": {
              // Parse the final metadata blob
              let meta: StreamResponseMeta | undefined;
              try {
                meta = payload
                  ? (JSON.parse(payload) as StreamResponseMeta)
                  : undefined;
              } catch {
                // If it's not JSON, finish without meta
              }
              return meta;
            }
            default: {
              // Unknown tag — ignore and continue
              break;
            }
          }
        }
      }
    } catch (err) {
      console.error("Error fetching response:", err);

      // Remove loading msg from allMessages, preserving hidden branch messages
      setChats((prev) =>
        prev.map((c) =>
          String(c.id) === String(currentChat)
            ? {
                ...c,
                messages: (c.messages || []).filter((m) => !m.isLoading),
                error: "Failed to get response",
                isLoading: false,
              }
            : c,
        ),
      );

      return null;
    }
  };

  const handleSendMessage = async (
    messageContent: string,
    files: File[] = [],
    modelName: string,
  ) => {
    let content = messageContent;
    if ((chat?.error || chat?.limit) && messages?.length > 0 && !content) {
      content = messages[messages.length - 1].content ?? "";
    }

    if (files?.length) {
      const fileNames = files.map((file) => file.name).join(", ");
      content += `\n\nAttached files: ${fileNames}`;
    }

    // Chain temp messages into the parent tree so visibleMessages picks them up
    const lastVisible = messages[messages.length - 1];
    const preferredParentId =
      selectedBranchLeafId != null ? selectedBranchLeafId : lastVisible?.id;
    const requestPath =
      selectedBranchLeafId != null
        ? getPathToNode(selectedBranchLeafId)
        : messages;

    const tempMsg: ChatMessage = {
      id: messages.length.toString() + "_",
      role: "user",
      content: content,
      parent_id:
        preferredParentId != null ? (preferredParentId as number) : undefined,
    };
    const loadingMsg: ChatMessage = {
      id: (messages.length + 1).toString() + "_",
      role: "assistant",
      isLoading: true,
      parent_id: tempMsg.id as number,
    };

    if (!currentChat) {
      const nextMessages = [...requestPath, tempMsg, loadingMsg];
      messages = nextMessages;
      addTempChatMessages("new-chat", nextMessages);
    } else {
      // Use allMessages (not visibleMessages) to preserve hidden branch messages
      if (!chat?.error && !chat?.limit) {
        const updatedAll = [...allMessages, tempMsg, loadingMsg];
        setChatMessages(currentChat as string | number, updatedAll);
        messages = [...requestPath, tempMsg, loadingMsg];
      }
      if (chat?.error || chat?.limit) {
        const updatedAll = [...allMessages, loadingMsg];
        setChatMessages(currentChat as string | number, updatedAll);
        messages = [...requestPath, loadingMsg];
      }
    }

    const isNewChat = currentChat === "new-chat" || !currentChat;

    const response = (await sendMessage(
      content,
      files,
      modelName,
      selectedAccount,
      messages,
      preferredParentId ?? null,
    )) as StreamResponseMeta;

    const newMessage = response ? response.answer : null;

    const responseChat = response?.chat_session as ChatSession;
    const responseUserMessage = response?.user_message as ChatMessage;
    const responseAiMessage = response?.system_answer as ChatMessage;
    const daylyToken = response?.ai_free_daily_tokens_available;
    const aiTokensAvailable = response?.ai_tokens_available;

    if (newMessage) {
      updateTokens(daylyToken!, aiTokensAvailable!);

      if (isNewChat) {
        newChatAdded(responseChat, responseUserMessage, responseAiMessage);
      } else
        newMessagesAdded(
          responseChat.id,
          tempMsg.id,
          responseUserMessage,
          loadingMsg.id,
          responseAiMessage,
        );
    }
  };

  // ─── Branch: start editing (populate input) ─────────────────────
  const editingMessageRef = useRef<string | number | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const startEdit = useCallback(
    (messageId: string | number) => {
      const msg = visibleMessages.find(
        (m) => String(m.id) === String(messageId),
      );
      if (!msg) return;
      // Populate the chat input with the message content
      const chatId = String(currentChat ?? "new-chat");
      setDrafts((prev) => ({ ...prev, [chatId]: msg.content ?? "" }));
      // Restore the account context from the message
      if (msg.context?.account) {
        const match = accounts.find(
          (a: any) => a.id === msg.context!.account.id,
        );
        setSelectedAccount(match ?? msg.context.account);
      }
      // Remember which message we're editing
      editingMessageRef.current = messageId;
      setIsEditing(true);
    },
    [visibleMessages, accounts, currentChat, setSelectedAccount],
  );

  const cancelEdit = useCallback(() => {
    editingMessageRef.current = null;
    setIsEditing(false);
    const chatId = String(currentChat ?? "new-chat");
    setDrafts((prev) => ({ ...prev, [chatId]: "" }));
  }, [currentChat]);

  // ─── Branch: edit & resend ──────────────────────────────────────
  const editAndResend = async (
    messageId: string | number,
    newContent: string,
  ) => {
    if (!newContent.trim() || !currentChat || chat?.isLoading) return;

    const editIdx = visibleMessages.findIndex(
      (m) => String(m.id) === String(messageId),
    );
    if (editIdx === -1) return;

    // Compute correct parent: same parent as the edited message (making new msg a sibling).
    // For legacy messages without parent_id, fall back to the preceding message in the visible list.
    let branchParentId: number | string | null | undefined =
      visibleMessages[editIdx].parent_id;
    if (branchParentId == null && editIdx > 0) {
      branchParentId = visibleMessages[editIdx - 1].id as number;
    }

    // Keep messages before the edited one, add temp user + loading
    const tempUser: ChatMessage = {
      id: "branch_user_" + Date.now(),
      role: "user",
      content: newContent,
      parent_id: branchParentId,
    };
    const tempLoading: ChatMessage = {
      id: "branch_loading_" + Date.now(),
      role: "assistant",
      isLoading: true,
      parent_id: tempUser.id as number,
    };
    // Replace allMessages: keep everything, add temp msgs
    const tempAll = [...allMessages, tempUser, tempLoading];
    setChatMessages(currentChat, tempAll, null, false, true);
    // Select the new branch so visiblePath picks it up
    if (branchParentId != null) {
      setActiveBranches((prev) => ({
        ...prev,
        [String(branchParentId)]: tempUser.id,
      }));
    }

    try {
      const context = selectedAccount
        ? {
            account: {
              id: selectedAccount.id,
              name: selectedAccount.name,
              broker_type: selectedAccount.broker_type,
            },
          }
        : null;

      const stream = (await branchStreamAnswer(
        messageId,
        newContent,
        context,
      )) as AsyncIterable<string>;

      let rawBuffer = "";
      let full_reply = "";

      for await (const rawChunk of stream) {
        rawBuffer += rawChunk;
        const { chunks, remaining } = extractCompleteChunks(rawBuffer);
        rawBuffer = remaining;

        for (const ch of chunks) {
          switch (ch.tag) {
            case "data": {
              full_reply += ch.payload;
              setTypingMessage(currentChat!, tempLoading.id, full_reply);
              break;
            }
            case "limit": {
              const cleaned = tempAll.filter(
                (m) => m.id !== tempUser.id && m.id !== tempLoading.id,
              );
              setChatMessages(currentChat, cleaned, null, true);
              return;
            }
            case "error":
              throw new Error(ch.payload || "Branch stream error");
            case "done": {
              let meta: StreamResponseMeta | undefined;
              try {
                meta = ch.payload ? JSON.parse(ch.payload) : undefined;
              } catch {
                /* ignore malformed JSON in done payload */
              }
              if (meta) {
                const realUser = meta.user_message as ChatMessage;
                const realAi = meta.system_answer as ChatMessage;
                updateTokens(
                  meta.ai_free_daily_tokens_available!,
                  meta.ai_tokens_available!,
                );

                // Replace temp messages with real ones in allMessages
                setChats((prev) =>
                  prev.map((c) => {
                    if (String(c.id) !== String(currentChat)) return c;
                    const updated = (c.messages || []).map((msg) => {
                      if (String(msg.id) === String(tempUser.id))
                        return {
                          ...msg,
                          id: realUser.id,
                          parent_id: realUser.parent_id,
                          context: realUser.context,
                        };
                      if (String(msg.id) === String(tempLoading.id))
                        return {
                          ...msg,
                          id: realAi.id,
                          content: realAi.content,
                          parent_id: realAi.parent_id,
                          context: realAi.context,
                          isLoading: false,
                        };
                      return msg;
                    });
                    return { ...c, messages: updated, isLoading: false };
                  }),
                );
                // Point active branch to the real user message
                if (realUser.parent_id != null) {
                  setActiveBranches((prev) => ({
                    ...prev,
                    [String(realUser.parent_id)]: realUser.id,
                  }));
                }
              }
              return;
            }
          }
        }
      }
    } catch (err) {
      console.error("Branch error:", err);
      // Remove temp messages on error
      const cleaned = allMessages.filter(
        (m) => m.id !== tempUser.id && m.id !== tempLoading.id,
      );
      setChatMessages(
        currentChat as string | number,
        cleaned,
        "Failed to get response",
      );
    }
  };

  // ─── Branch: switch to a sibling ──────────────────────────────
  const switchToBranch = useCallback(
    async (parentId: string | number, targetSiblingId: string | number) => {
      console.log("[switchToBranch]", { parentId, targetSiblingId });

      // Update active selection
      setActiveBranches((prev) => ({
        ...prev,
        [String(parentId)]: targetSiblingId,
      }));

      // Check if we already have that sibling's descendants
      const hasTarget = normalizedMessages.some(
        (m) => String(m.id) === String(targetSiblingId),
      );
      console.log("[switchToBranch] hasTarget:", hasTarget);
      if (!hasTarget) return; // shouldn't happen

      // Check if descendants are loaded (the sibling should have at least one child unless it's a leaf)
      const hasChildren = normalizedMessages.some(
        (m) => String(m.parent_id) === String(targetSiblingId),
      );
      console.log("[switchToBranch] hasChildren:", hasChildren);
      if (hasChildren) return; // We have everything, visible path will recalculate

      // Fetch the branch descendants from server
      try {
        const data = await switchBranchAPI<{ messages: ChatMessage[] }>(
          targetSiblingId,
        );
        if (data.messages?.length > 1) {
          // First message is the sibling itself (already in allMessages), rest are descendants
          const descendants = data.messages.slice(1);
          setChats((prev) =>
            prev.map((c) =>
              String(c.id) === String(currentChat)
                ? { ...c, messages: [...(c.messages || []), ...descendants] }
                : c,
            ),
          );
        }
      } catch (err) {
        console.error("Switch branch error:", err);
      }
    },
    [normalizedMessages, currentChat, setChats],
  );

  const setMessageLikedValue = useCallback(
    (messageId: string | number, liked: boolean | null) => {
      setChats((prev) =>
        prev.map((chatSession) => {
          if (String(chatSession.id) !== String(currentChat))
            return chatSession;
          return {
            ...chatSession,
            messages: (chatSession.messages || []).map((message) =>
              String(message.id) === String(messageId)
                ? { ...message, liked }
                : message,
            ),
          };
        }),
      );
    },
    [currentChat, setChats],
  );

  const likeMessage = useCallback(
    async (messageId: string | number) => {
      setMessageLikedValue(messageId, true);
      try {
        await likeMessageAPI(messageId);
      } catch (error) {
        console.error("Like message error:", error);
        setMessageLikedValue(messageId, null);
      }
    },
    [setMessageLikedValue],
  );

  const dislikeMessage = useCallback(
    async (messageId: string | number) => {
      setMessageLikedValue(messageId, false);
      try {
        await dislikeMessageAPI(messageId);
      } catch (error) {
        console.error("Dislike message error:", error);
        setMessageLikedValue(messageId, null);
      }
    },
    [setMessageLikedValue],
  );

  const handleSubmit = async (
    e?: React.FormEvent | null,
    message: string | null = null,
  ) => {
    e?.preventDefault();

    const msg = input.trim() || message || "";

    if ((msg || files.length > 0) && !chat?.isLoading) {
      const editId = editingMessageRef.current;
      setInput("");
      setFiles([]);
      editingMessageRef.current = null;
      setIsEditing(false);

      try {
        if (editId) {
          // Branch edit: resend from the edited message
          await editAndResend(editId, msg);
        } else {
          await handleSendMessage(msg, files, model.name);
        }
      } catch (error) {
        console.error("Error sending message:", error);
      }
    }
  };

  return {
    chat,
    messages,
    allMessages,
    siblingsMap,
    activeBranches,

    input,
    files,
    setInput,
    setFiles,
    handleSubmit,

    models: AI_MODELS,
    model,
    setModel,

    selectedAccount,
    setSelectedAccount,

    startEdit,
    isEditing,
    editingMessageId: editingMessageRef.current,
    cancelEdit,
    switchToBranch,
    likeMessage,
    dislikeMessage,
  };
}
