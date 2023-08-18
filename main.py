import os
import telebot
from flask import Flask
import logging
from collections import Counter

from yolo_inference import predict
from notion import smart_update_notion


bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'), parse_mode='MARKDOWN')
app = Flask(__name__)
temp_path = "photo.png"


def detected_labels_to_message(counter):
    total_count = counter.total()
    message = f"Total: {total_count}\n\n" + "\n".join([f"{label}: {count}" for label, count in counter.items()])
    return message


def handle_image(message):
    # -1 to get the best quality
    file_path = bot.get_file(message.photo[-1].file_id).file_path
    file = bot.download_file(file_path)
    with open(temp_path, "wb") as code:
        code.write(file)
    try:
        # We need 0 because we are working only with one image right now
        prediction = predict(image_path=temp_path)[0]
    except Exception as e:
        print(f'Error in prediction with exception: {e}')
        bot.reply_to(message, 'Error in prediction')
        return
    detected_labels = [prediction.names[name] for name in prediction.boxes.cls.tolist()]
    all_labels = [prediction.names[name] for name in prediction.names]
    undetected_labels = [label for label in all_labels if label not in detected_labels]
    print(f"Detected: {detected_labels}")
    print(f"Undetected: {undetected_labels}")
    detected_labels_counter = Counter(detected_labels)
    smart_update_notion(detected_labels_counter, undetected_labels)
    bot.reply_to(message, detected_labels_to_message(detected_labels_counter))


def main():
    @bot.message_handler(content_types=['photo'])
    def handle_photo(message):
        handle_image(message)

    bot.infinity_polling()


if __name__ == '__main__':
    # Telegram Bot Token
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    main()
    app.run(host='0.0.0.0', port=5000)  # Run Flask app on port 5000
