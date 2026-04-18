# Spec: feature-001 — LLMOps CI/CD Pipeline

## Status
`approved`

## Author
Antigravity (AI Engineer)

## Date
2026-04-18

---

## 1. User
- Persona: Backend engineer / ML engineer làm việc trên `application-support`
- Role: Developer push code lên GitHub và cần biết ngay khi prompt thay đổi gây regression

## 2. Problem

Hiện tại `application-support` đã có CI/CD pipeline đầy đủ (format → lint → tests → docker → trivy),
nhưng **không có bất kỳ bước nào kiểm soát chất lượng LLM output**.

Cụ thể:
- Khi ai đó chỉnh file prompt JSON (`sop_outline_v1.json`, `cover_letter_generation_v1.json`, v.v.)
  thì pipeline CI **không phát hiện** ra output LLM có thể thay đổi xấu đi.
- Không có test nào kiểm tra: prompt có render đúng không? placeholder có bị thiếu không?
  Token count có vượt model limit không?
- Không có baseline để so sánh chất lượng output giữa các commit.
- `mysql_llm_call_log_repo` đã log `tokens, latency, success` nhưng không log **quality score**.

## 3. Goal

Thêm một **LLMOps stage** vào CI/CD pipeline của `application-support` gồm 3 lớp:

1. **Prompt Lint** (chạy mọi PR, free, < 30s): validate cấu trúc prompt, token count, placeholder
2. **Prompt Diff Alert** (chạy mọi PR, free): tự động comment lên PR khi file prompt thay đổi
3. **LLM Eval / Quality Gate** (chạy chỉ khi push lên `main`, dùng real API): chạy golden test cases,
   dùng LLM-as-judge chấm điểm, so sánh với baseline, fail nếu regression

## 4. Expected Behavior

### PR flow:
1. Developer mở PR có sửa `app/llm/` hoặc bất kỳ file prompt nào
2. Job `prompt-lint` chạy: kiểm tra JSON valid, tất cả placeholder được inject, token count ước tính < 80% limit
3. Job `prompt-diff-alert` chạy: detect file prompt thay đổi → comment lên PR liệt kê file nào đổi và cảnh báo
4. Nếu prompt-lint fail → PR bị block merge

### Push to main flow:
1. Sau khi docker-build thành công, job `llm-eval` chạy
2. Script `scripts/run_evals.py` load golden test cases từ `tests/llm/fixtures/`
3. Với mỗi test case: gọi LLM thật → nhận output → dùng LLM-as-judge (GPT-4o-mini) chấm điểm
4. So sánh average score với `EVAL_BASELINE_SCORE` (GitHub repo variable)
5. Nếu score giảm > 0.5 điểm so với baseline → pipeline fail
6. Nếu pass → cập nhật baseline mới vào repo variable

## 5. Acceptance Criteria

- [ ] `prompt-lint` job chạy thành công trên PR không có thay đổi prompt
- [ ] `prompt-lint` job fail khi có prompt file JSON invalid
- [ ] `prompt-lint` job fail khi token count ước tính vượt 80% model limit
- [ ] `prompt-diff-alert` tạo comment trên PR khi có file trong `app/llm/` thay đổi
- [ ] `llm-eval` job chỉ chạy khi push lên `main`
- [ ] `llm-eval` job fail khi score trung bình giảm > 0.5 so với baseline
- [ ] `llm-eval` upload artifact `eval_results.json` sau mỗi lần chạy
- [ ] Tất cả jobs mới follow cùng Python version và caching pattern với CI hiện tại
- [ ] `tests/llm/test_prompt_lint.py` có thể chạy local không cần API key
- [ ] Có ít nhất 3 golden test cases cho SOP và 2 cho cover letter

## 6. Non-Goals

- Không implement streaming evaluation (chỉ request/response đơn)
- Không tích hợp LangSmith, Promptfoo, hay bất kỳ external LLMOps platform nào
- Không thêm eval cho `checklist_service` hay `deadline_service` trong feature này
- Không thay đổi logic business của bất kỳ service nào hiện có
- Không thêm database migration mới

## 7. Open Questions

- [ ] GPT-4o-mini dùng làm judge có đủ reliable chưa, hay cần dùng GPT-4o?
- [ ] Baseline score lưu vào GitHub repo variable hay commit vào repo dưới dạng file?
- [ ] Nếu `OPENAI_API_KEY` không được set ở CI → llm-eval skip hay fail?
- [ ] Cost budget cho mỗi lần chạy eval (ước tính ~$0.50-$1.00/run)?

---

## Checklist before approval
- [ ] User và problem đã được định nghĩa rõ ràng
- [ ] Acceptance criteria có thể kiểm tra được
- [ ] Non-goals đã được liệt kê
- [ ] Không có architectural assumption nào chưa được approve
- [ ] Reviewed by human gate owner
