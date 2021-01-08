//selecting all required elements
const start_btn = document.querySelector(".start_btn button");
const info_box = document.querySelector(".info_box");
const exit_btn = info_box.querySelector(".buttons .quit");
const continue_btn = info_box.querySelector(".buttons .restart");
const quiz_box = document.querySelector(".quiz_box");
const result_box = document.querySelector(".result_box");
const option_list = document.querySelector(".option_list");
const time_line = document.querySelector("header .time_line");
const timeText = document.querySelector(".timer .time_left_txt");
const timeCount = document.querySelector(".timer .timer_sec");

// Base points granted per each question
const userScore = 10;

// Controller data for quiz (username, quiz category, default answer time)
let flaskData = $('#my-data').data();
let timeValue = flaskData['time'];

// Questions specific counters
let questionCount = 0;
let questionNumber = 1;


// Counter specific variables
let counter;
let counterLine;
let widthValue = 0;

// Quiz statistics
let good = 0;
let wrong = 0;
let totalScore = 0;
let combo = 0;
let maxCombo = 0;
let totalTime = 0;

const restart_quiz = result_box.querySelector(".buttons .restart");
const quit_quiz = result_box.querySelector(".buttons .quit");

// if startQuiz button clicked
start_btn.onclick = ()=>{
    info_box.classList.add("activeInfo"); //show info box
}

// if exitQuiz button clicked
exit_btn.onclick = ()=>{
    location.href = '/'+flaskData['user']+'/'+'prepare_quiz'; //reload the current window
}

// if continueQuiz button clicked
continue_btn.onclick = ()=>{
    info_box.classList.remove("activeInfo"); //hide info box
    quiz_box.classList.add("activeQuiz"); //show quiz box
    showQuetions(0); //calling showQestions function
    queCounter(1); //passing 1 parameter to queCounter
    startTimer(timeValue); //calling startTimer function
    startTimerLine(0); //calling startTimerLine function
}

// Function to return javascirpt variables into flask controller and redirect user
function sendStats(redirect){
    $.ajax({
    type: "POST",
    url: redirect,
    contentType: "application/json",
    data: JSON.stringify(
        {
            good: good,
            wrong : wrong,
            totalScore : totalScore,
            totalTime : totalTime
    },),
    dataType: "json",
    success: function(response) {
        console.log(response);
    },
    error: function(err) {
        console.log(err);
    }
});
}

// if restartQuiz button clicked
restart_quiz.onclick = ()=>{
    sendStats('learn');
    quiz_box.classList.add("activeQuiz"); //show quiz box
    result_box.classList.remove("activeResult"); //hide result box
    timeValue = flaskData['time'];
    questionCount = 0;
    questionNumber = 1;
    widthValue = 0;
    good = 0;
    wrong = 0;
    totalScore = 0;
    combo = 0;
    maxCombo = 0;
    showQuetions(questionCount); //calling showQestions function
    queCounter(questionNumber); //passing questionNumber value to queCounter
    clearInterval(counter); //clear counter
    clearInterval(counterLine); //clear counterLine
    startTimer(timeValue); //calling startTimer function
    startTimerLine(widthValue); //calling startTimerLine function
    timeText.textContent = "Pozostały czas"; //change the text of timeText to Time Left
    next_btn.classList.remove("show"); //hide the next button
}

// if quitQuiz button clicked
quit_quiz.onclick = ()=>{
    sendStats('learn');
    location.href = '/home'; //reload the current window
}

const next_btn = document.querySelector("footer .next_btn");
const bottom_ques_counter = document.querySelector("footer .total_que");

// if Next Que button clicked
next_btn.onclick = ()=>{
    if(questionCount < questions.length - 1){ //if question count is less than total question length
        questionCount++; //increment the questionCount value
        questionNumber++; //increment the questionNumber value
        showQuetions(questionCount); //calling showQestions function
        queCounter(questionNumber); //passing questionNumber value to queCounter
        clearInterval(counter); //clear counter
        clearInterval(counterLine); //clear counterLine
        startTimer(timeValue); //calling startTimer function
        startTimerLine(widthValue); //calling startTimerLine function
        timeText.textContent = "Pozostały czas"; //change the timeText to Time Left
        next_btn.classList.remove("show"); //hide the next button
    }else{
        clearInterval(counter); //clear counter
        clearInterval(counterLine); //clear counterLine
        showResult(); //calling showResult function
    }
}

// getting questions and options from array
function showQuetions(index){
    const que_text = document.querySelector(".que_text");

    //creating a new span and div tag for question and option and passing the value using array index
    let que_tag = '<span>'+ questions[index].numb + ". " + questions[index].question +'</span>';
    let option_tag = '<div class="option"><span>'+ questions[index].options[0] +'</span></div>'
    + '<div class="option"><span>'+ questions[index].options[1] +'</span></div>'
    + '<div class="option"><span>'+ questions[index].options[2] +'</span></div>'
    + '<div class="option"><span>'+ questions[index].options[3] +'</span></div>';
    que_text.innerHTML = que_tag; //adding new span tag inside que_tag
    option_list.innerHTML = option_tag; //adding new div tag inside option_tag
    
    const option = option_list.querySelectorAll(".option");

    // set onclick attribute to all available options
    for(i=0; i < option.length; i++){
        option[i].setAttribute("onclick", "optionSelected(this)");
    }
}
// creating the new div tags which for icons
let tickIconTag = '<div class="icon tick"></div>';
let crossIconTag = '<div class="icon cross"></div>';

//if user clicked on option
function optionSelected(answer){
    clearInterval(counter); //clear counter
    clearInterval(counterLine); //clear counterLine
    let userAns = answer.textContent; //getting user selected option
    let correcAns = questions[questionCount].answer; //getting correct answer from array
    const allOptions = option_list.children.length; //getting all option items
    
    if(userAns == correcAns){ //if user selected option is equal to array's correct answer
        combo += 1;
        good += 1;
        if(combo >= maxCombo){
            maxCombo = combo;
        }
        totalScore += combo * userScore;
        answer.classList.add("correct"); //adding green color to correct selected option
        answer.insertAdjacentHTML("beforeend", tickIconTag); //adding tick icon to correct selected option

    }else{
        wrong += 1;
        combo =  0;
        if(combo >= maxCombo) {
            maxCombo = combo;
        }
        answer.classList.add("incorrect"); //adding red color to correct selected option
        answer.insertAdjacentHTML("beforeend", crossIconTag); //adding cross icon to correct selected option

        for(i=0; i < allOptions; i++){
            if(option_list.children[i].textContent == correcAns){ //if there is an option which is matched to an array answer 
                option_list.children[i].setAttribute("class", "option correct"); //adding green color to matched option
                option_list.children[i].insertAdjacentHTML("beforeend", tickIconTag); //adding tick icon to matched option
            }
        }
    }
    for(i=0; i < allOptions; i++){
        option_list.children[i].classList.add("disabled"); //once user select an option then disabled all options
    }
    next_btn.classList.add("show"); //show the next button if user selected any option
}

function showResult(){
    info_box.classList.remove("activeInfo"); //hide info box
    quiz_box.classList.remove("activeQuiz"); //hide quiz box
    result_box.classList.add("activeResult"); //show result box
    const scoreText = result_box.querySelector(".score_text");
    let scoreTag =
        '' +
        '<span>Gratulacje! Zdobyłeś <p>'+ totalScore +'</p>punktów</span>'+
        '<span>Dobre odpowiedzi: <p>'+ good +'</p></span>'+
        '<span>Złe odpowiedzi: <p>'+ wrong +'</p></span>'+
        '<span>Dobre odpowiedzi z rzędu: <p>'+ maxCombo +'</p></span>'+
        '<span>Czas: <p>'+ totalTime +' sekund</p></span>';
    scoreText.innerHTML = scoreTag;  //adding new span tag inside score_Text
}

function startTimer(time){
    counter = setInterval(timer, 1000);
    function timer(){
        timeCount.textContent = time; //changing the value of timeCount with time value
        time--; //decrement the time value
        totalTime++;
        if(time < 9){ //if timer is less than 9
            let addZero = timeCount.textContent; 
            timeCount.textContent = "0" + addZero; //add a 0 before time value
        }
        if(time < 0){ //if timer is less than 0
            clearInterval(counter); //clear counter
            timeText.textContent = "Czas upłynął"; //change the time text to time off
            const allOptions = option_list.children.length; //getting all option items
            let correcAns = questions[questionCount].answer; //getting correct answer from array
            for(i=0; i < allOptions; i++){
                if(option_list.children[i].textContent == correcAns){ //if there is an option which is matched to an array answer
                    option_list.children[i].setAttribute("class", "option correct"); //adding green color to matched option
                    option_list.children[i].insertAdjacentHTML("beforeend", tickIconTag); //adding tick icon to matched option
                }
            }
            for(i=0; i < allOptions; i++){
                option_list.children[i].classList.add("disabled"); //once user select an option then disabled all options
            }
            next_btn.classList.add("show"); //show the next button if user selected any option
        }
    }
}

function startTimerLine(time){
    counterLine = setInterval(timer, 29);
    function timer(){
        time += 1; //upgrading time value with 1
        time_line.style.width = (time * 15/timeValue) + "px"; // increasing width of time_line with px by time value
        if(time > (timeValue/15 * 549)){ // If the time value is greater than time line width
            clearInterval(counterLine); //Clear updating time_line
        }
    }
}

function queCounter(index){
    //creating a new span tag and passing the question number and total question
    let totalQueCounTag = '<span><p>'+ index +'</p> z <p>'+ questions.length +'</p> Pytań</span>';
    bottom_ques_counter.innerHTML = totalQueCounTag;  //adding new span tag inside bottom_ques_counter
}