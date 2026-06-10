document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const resetBtn = document.getElementById('reset-btn');
    const countdownEl = document.getElementById('countdown');
    const resultEl = document.getElementById('game-result');
    const gestureOverlay = document.getElementById('gesture-overlay');
    const cpuMoveIcon = document.getElementById('cpu-move-icon');

    const userScoreEl = document.getElementById('user-score');
    const cpuScoreEl = document.getElementById('cpu-score');
    const drawScoreEl = document.getElementById('draw-score');

    const soundWin = document.getElementById('sound-win');
    const soundLose = document.getElementById('sound-lose');
    const soundDraw = document.getElementById('sound-draw');

    const moveEmoji = {
        'Stone': '✊',
        'Paper': '✋',
        'Scissors': '✌️',
        'None': '❓'
    };

    let isGaming = false;

    // Polling for current gesture to update overlay
    setInterval(async () => {
        if (!isGaming) {
            try {
                const response = await fetch('/get_current_gesture');
                const data = await response.json();
                gestureOverlay.textContent = `Detected: ${data.gesture}`;
            } catch (e) {
                console.error("Error fetching gesture", e);
            }
        }
    }, 500);

    async function startSequence() {
        if (isGaming) return;
        isGaming = true;

        startBtn.disabled = true;
        resetBtn.disabled = true;
        resultEl.textContent = "Get Ready...";
        cpuMoveIcon.textContent = '❓';

        // Countdown 3, 2, 1
        for (let i = 3; i > 0; i--) {
            countdownEl.textContent = i;
            countdownEl.style.opacity = '1';
            await new Promise(r => setTimeout(r, 800));
            countdownEl.style.opacity = '0';
            await new Promise(r => setTimeout(r, 200));
        }

        countdownEl.textContent = 'PLAY!';
        countdownEl.style.opacity = '1';

        // Final Action: Get Moves
        const [userRes, cpuRes] = await Promise.all([
            fetch('/get_current_gesture'),
            fetch('/get_computer_move')
        ]);

        const userData = await userRes.json();
        const cpuData = await cpuRes.json();

        const userMove = userData.gesture;
        const cpuMove = cpuData.move;

        cpuMoveIcon.textContent = moveEmoji[cpuMove];
        cpuMoveIcon.classList.add('pop');
        setTimeout(() => cpuMoveIcon.classList.remove('pop'), 300);

        await determineWinner(userMove, cpuMove);

        countdownEl.style.opacity = '0';
        isGaming = false;
        startBtn.disabled = false;
        resetBtn.disabled = false;
    }

    async function determineWinner(user, cpu) {
        if (user === 'None') {
            resultEl.textContent = "No hand detected! Try again.";
            return;
        }

        let result = "";
        let scoreKey = "";

        if (user === cpu) {
            result = `DRAW! Both chose ${user}`;
            scoreKey = "draw";
            soundDraw.play();
        } else if (
            (user === 'Stone' && cpu === 'Scissors') ||
            (user === 'Paper' && cpu === 'Stone') ||
            (user === 'Scissors' && cpu === 'Paper')
        ) {
            result = `YOU WIN! ${user} beats ${cpu}`;
            scoreKey = "user";
            soundWin.play();
        } else {
            result = `CPU WINS! ${cpu} beats ${user}`;
            scoreKey = "computer";
            soundLose.play();
        }

        resultEl.textContent = result;

        // Update backend score and sync UI
        const response = await fetch(`/add_score/${scoreKey}`);
        const updatedScores = await response.json();

        userScoreEl.textContent = updatedScores.user_score;
        cpuScoreEl.textContent = updatedScores.computer_score;
        drawScoreEl.textContent = updatedScores.draws;
    }

    async function resetGame() {
        const response = await fetch('/reset');
        if (response.ok) {
            userScoreEl.textContent = '0';
            cpuScoreEl.textContent = '0';
            drawScoreEl.textContent = '0';
            resultEl.textContent = "Scores Reset!";
            cpuMoveIcon.textContent = '❓';
        }
    }

    startBtn.addEventListener('click', startSequence);
    resetBtn.addEventListener('click', resetGame);
});
