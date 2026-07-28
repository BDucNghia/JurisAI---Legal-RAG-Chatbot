import json
from tqdm import tqdm
from prompt_formatter import create_generation_prompt_for_finetune

INPUT_FILE = "K=10/judge_data.jsonl"
OUTPUT_FILE = "K=10/dpo_dataset.jsonl"


def convert_to_dpo_format():
    print(f"Đang đọc từ '{INPUT_FILE}' và chuyển đổi sang định dạng DPO...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f_in, \
            open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for line in tqdm(f_in, desc="Đang xử lý dữ liệu"):
            data = json.loads(line)

            question = data['question']
            context = data['context']
            chosen_answer = data['chosen_answer']
            rejected_answer = data['rejected_answer']

            # 1. Tạo phần prompt chung (không có câu trả lời)
            prompt = create_generation_prompt_for_finetune(context, question)

            # 2. Tạo chuỗi hoàn chỉnh cho câu trả lời được chọn và bị từ chối
            # Dấu cách ở giữa là quan trọng
            chosen_full_text = prompt + " " + chosen_answer
            rejected_full_text = prompt + " " + rejected_answer

            # 3. Tạo đối tượng JSON mới với 3 cột yêu cầu
            dpo_record = {
                "prompt": prompt,
                "chosen": chosen_full_text,
                "rejected": rejected_full_text
            }

            f_out.write(json.dumps(dpo_record, ensure_ascii=False) + "\n")

    print(f"Hoàn tất! Dữ liệu đã được chuyển đổi và lưu tại '{OUTPUT_FILE}'")


if __name__ == "__main__":
    convert_to_dpo_format()