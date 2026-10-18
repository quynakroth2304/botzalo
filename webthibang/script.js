// --- PHẦN 1: DỮ LIỆU (DATABASE) ---
// Để chạy thật, bạn cần điền đầy đủ 200-600 câu vào đây.
// isCritical: true nghĩa là câu điểm liệt.
const database = [
    {
        id: 1,
        license: ["A1", "A2", "B1", "B2"], // Câu này dùng cho bằng nào
        question: "Phần của đường bộ được sử dụng cho các phương tiện giao thông qua lại là gì?",
        image: "",
        options: ["Phần mặt đường và lề đường.", "Phần đường xe chạy.", "Phần đường xe cơ giới."],
        answer: 1, // Index của đáp án đúng (bắt đầu từ 0)
        isCritical: false
    },
    {
        id: 2,
        license: ["A1", "A2"],
        question: "Biển nào cấm xe đạp đi vào?",
        image: "https://hoclaixecaptoc.com/wp-content/uploads/2018/12/bien-cam-xe-dap.jpg", // Thay link ảnh thật vào đây
        options: ["Biển 1", "Biển 2", "Biển 3"],
        answer: 1,
        isCritical: false
    },
    {
        id: 3,
        license: ["A1", "A2", "B1", "B2"],
        question: "Hành vi đua xe trái phép có bị nghiêm cấm không?",
        image: "",
        options: ["Không bị nghiêm cấm.", "Bị nghiêm cấm tuỳ trường hợp.", "Bị nghiêm cấm."],
        answer: 2,
        isCritical: true // Câu điểm liệt
    },
    {
        id: 4,
        license: ["B1", "B2"],
        question: "Người lái xe được dừng xe, đỗ xe trong khu vực an toàn của đường sắt không?",
        image: "",
        options: ["Được dừng nhưng không được đỗ.", "Không được dừng, đỗ.", "Được đỗ xe."],
        answer: 1,
        isCritical: true
    }
    // ... BẠN HÃY COPY VÀ THÊM CÁC CÂU KHÁC VÀO ĐÂY ...
];

// --- PHẦN 2: ỨNG DỤNG (APP LOGIC) ---
const App = {
    currentLicense: null,
    examQuestions: [],
    wrongQuestions: JSON.parse(localStorage.getItem('wrong_questions')) || [], // Tải câu sai từ bộ nhớ

    // Cấu hình đề thi
    config: {
        'A1': { time: 19, total: 25, pass: 21 },
        'A2': { time: 19, total: 25, pass: 23 },
        'B1': { time: 20, total: 30, pass: 27 },
        'B2': { time: 22, total: 35, pass: 32 }
    },

    // Khởi động chọn bằng
    selectLicense: (type) => {
        App.currentLicense = type;
        document.getElementById('selection-screen').style.display = 'none';
        document.getElementById('dashboard-screen').style.display = 'block';
        document.getElementById('info-text').innerText = `Đang ôn thi hạng ${type}`;
    },

    resetToHome: () => {
        clearInterval(Quiz.timerInterval);
        document.getElementById('dashboard-screen').style.display = 'none';
        document.getElementById('quiz-screen').style.display = 'none';
        document.getElementById('result-overlay').style.display = 'none';
        document.getElementById('selection-screen').style.display = 'block';
        document.getElementById('timer').style.display = 'none';
        document.getElementById('footer-action').style.display = 'none';
    },

    // Chế độ 1: Thi ngẫu nhiên
    startRandomExam: () => {
        // Lọc câu hỏi theo bằng lái
        const pool = database.filter(q => q.license.includes(App.currentLicense));
        
        // Trộn câu hỏi ngẫu nhiên
        const shuffled = pool.sort(() => 0.5 - Math.random());
        
        // Lấy số lượng câu theo quy định (ví dụ A1 lấy 25 câu)
        const limit = App.config[App.currentLicense].total;
        App.examQuestions = shuffled.slice(0, limit);

        Quiz.start(App.examQuestions, true); // true = có tính giờ
    },

    // Chế độ 2: Ôn tập câu sai
    reviewWrongSentences: () => {
        if (App.wrongQuestions.length === 0) {
            alert("Bạn chưa có câu nào làm sai!");
            return;
        }
        // Tìm chi tiết câu hỏi từ ID đã lưu
        const wrongData = database.filter(q => App.wrongQuestions.includes(q.id));
        Quiz.start(wrongData, false); // false = không tính giờ
    },
    
    // Chế độ 3: Ôn tập tất cả
    startReviewMode: () => {
         const pool = database.filter(q => q.license.includes(App.currentLicense));
         Quiz.start(pool, false);
    },

    backToDashboard: () => {
        if(confirm("Bạn có chắc muốn thoát bài thi?")) {
            App.resetToHome();
            // Quay lại dashboard ngay lập tức (skip confirm nếu cần)
            document.getElementById('selection-screen').style.display = 'none';
            document.getElementById('dashboard-screen').style.display = 'block';
        }
    }
};

// --- PHẦN 3: LOGIC BÀI THI (QUIZ) ---
const Quiz = {
    questions: [],
    currentIndex: 0,
    score: 0,
    timerInterval: null,
    isExamMode: false,
    selectedOption: null,
    isAnswered: false,
    failedByCritical: false, // Rớt do câu điểm liệt

    start: (data, isExam) => {
        Quiz.questions = data;
        Quiz.currentIndex = 0;
        Quiz.score = 0;
        Quiz.isExamMode = isExam;
        Quiz.failedByCritical = false;

        document.getElementById('dashboard-screen').style.display = 'none';
        document.getElementById('quiz-screen').style.display = 'block';
        document.getElementById('footer-action').style.display = 'flex';
        
        // Setup Timer
        const timerDisplay = document.getElementById('timer');
        if (isExam) {
            timerDisplay.style.display = 'block';
            let totalSeconds = App.config[App.currentLicense].time * 60;
            
            clearInterval(Quiz.timerInterval);
            Quiz.timerInterval = setInterval(() => {
                totalSeconds--;
                const m = Math.floor(totalSeconds / 60);
                const s = totalSeconds % 60;
                timerDisplay.innerText = `${m}:${s < 10 ? '0'+s : s}`;
                if (totalSeconds <= 0) Quiz.finishExam();
            }, 1000);
        } else {
            timerDisplay.style.display = 'none';
        }

        Quiz.loadQuestion();
    },

    loadQuestion: () => {
        if (Quiz.currentIndex >= Quiz.questions.length) {
            Quiz.finishExam();
            return;
        }

        const q = Quiz.questions[Quiz.currentIndex];
        Quiz.isAnswered = false;
        Quiz.selectedOption = null;

        // Reset UI
        document.getElementById('question-progress').innerText = `Câu ${Quiz.currentIndex + 1}/${Quiz.questions.length}`;
        document.getElementById('q-text').innerText = (q.isCritical ? "[ĐIỂM LIỆT] " : "") + q.question;
        
        const imgEl = document.getElementById('q-image');
        if (q.image) {
            imgEl.src = q.image;
            imgEl.style.display = 'block';
        } else {
            imgEl.style.display = 'none';
        }

        const btn = document.getElementById('btn-submit');
        btn.innerText = "Xác nhận";
        btn.disabled = true;
        btn.style.background = '';

        // Render Options
        const container = document.getElementById('options-container');
        container.innerHTML = '';
        q.options.forEach((opt, idx) => {
            const div = document.createElement('div');
            div.className = 'option';
            div.innerText = `${idx + 1}. ${opt}`;
            div.onclick = () => Quiz.selectOption(idx, div);
            container.appendChild(div);
        });
    },

    selectOption: (idx, el) => {
        if (Quiz.isAnswered) return;
        
        Quiz.selectedOption = idx;
        document.querySelectorAll('.option').forEach(o => o.classList.remove('selected'));
        el.classList.add('selected');
        document.getElementById('btn-submit').disabled = false;
    },

    confirmAnswer: () => {
        if (Quiz.isAnswered) return;
        Quiz.isAnswered = true;

        const q = Quiz.questions[Quiz.currentIndex];
        const options = document.querySelectorAll('.option');
        const btn = document.getElementById('btn-submit');

        // Kiểm tra đúng sai
        if (Quiz.selectedOption === q.answer) {
            options[Quiz.selectedOption].classList.add('correct');
            btn.innerText = "Chính xác!";
            btn.style.background = "#4caf50";
            Quiz.score++;
            
            // Nếu làm đúng thì xóa khỏi danh sách "Hay sai" (nếu có)
            const wrongIdx = App.wrongQuestions.indexOf(q.id);
            if (wrongIdx > -1) {
                App.wrongQuestions.splice(wrongIdx, 1);
                localStorage.setItem('wrong_questions', JSON.stringify(App.wrongQuestions));
            }

        } else {
            options[Quiz.selectedOption].classList.add('wrong');
            options[q.answer].classList.add('correct');
            btn.innerText = "Sai rồi!";
            btn.style.background = "#f44336";

            // Logic điểm liệt
            if (q.isCritical && Quiz.isExamMode) {
                Quiz.failedByCritical = true;
            }

            // Lưu vào danh sách sai
            if (!App.wrongQuestions.includes(q.id)) {
                App.wrongQuestions.push(q.id);
                localStorage.setItem('wrong_questions', JSON.stringify(App.wrongQuestions));
            }
        }

        // Tự động chuyển câu sau 1.5s
        setTimeout(() => {
            Quiz.currentIndex++;
            Quiz.loadQuestion();
        }, 1500);
    },

    finishExam: () => {
        clearInterval(Quiz.timerInterval);
        document.getElementById('result-overlay').style.display = 'flex';
        
        const limit = App.config[App.currentLicense];
        const resultScore = document.getElementById('result-score');
        const resultMsg = document.getElementById('result-msg');
        
        resultScore.innerText = `${Quiz.score}/${limit.total}`;
        
        if (Quiz.failedByCritical) {
            resultMsg.innerText = "TRƯỢT (Sai câu điểm liệt)";
            resultMsg.style.color = "red";
        } else if (Quiz.score >= limit.pass) {
            resultMsg.innerText = "ĐẠT";
            resultMsg.style.color = "green";
        } else {
            resultMsg.innerText = "TRƯỢT (Không đủ điểm)";
            resultMsg.style.color = "red";
        }
    }
};