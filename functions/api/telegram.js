// Cloudflare Pages Function для Telegram бота
export async function onRequestPost(context) {
  const { request, env } = context;
  
  try {
    // Получаем данные от Telegram
    const update = await request.json();
    
    // Проверяем, что это сообщение
    if (update.message) {
      const message = update.message;
      const text = message.text;
      const chatId = message.chat.id;
      
      // Простая логика бота
      let response = "";
      
      if (text === "/start") {
        response = "Привет! Я твой ассистент по цифровой психологии по системе Миланы Тарба.\n\nВведите дату рождения в формате: 20.05.1997";
      } else if (text && text.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
        // Дата рождения
        response = `Спасибо дата принята: ${text}\nВведите имя`;
      } else if (text && text.match(/^[а-яёА-ЯЁa-zA-Z]+$/)) {
        // Имя
        response = "Ваши данные приняты начинаем анализ\n\n🔮 **АНАЛИЗ ПО ЦИФРОВОЙ ПСИХОЛОГИИ**\n\n*Анализ выполняется...*";
      } else {
        response = "❌ **Неверный формат.**\n\nВведите дату в формате `dd.mm.yyyy` или нажмите `/start`";
      }
      
      // Отправляем ответ
      await sendMessage(chatId, response, env.TELEGRAM_BOT_TOKEN);
    }
    
    return new Response("OK", { status: 200 });
    
  } catch (error) {
    console.error("Error:", error);
    return new Response("Error", { status: 500 });
  }
}

async function sendMessage(chatId, text, botToken) {
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  
  await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
      parse_mode: "Markdown"
    })
  });
}
