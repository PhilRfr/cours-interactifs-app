/// <reference path="onsenui.d.ts" />

function ui_error(err : string){
	ons.notification.alert(err);
}

function ui_login(){
	document.querySelector('#myNavigator').pushPage('main.html');
}

function ui_disconnect(){
	document.querySelector('#myNavigator').popPage();
	ons.notification.alert("You've been disconnected.");
	start_client();
}

function ui_kick(){
	document.querySelector('#myNavigator').popPage();
	ons.notification.alert("You've been kicked out.");
	start_client();
}

function ui_questions(questions){
	var tabs = document.querySelector("#tabs") as OnsTabbarElement;
	tabs.setActiveTab(1);
	var q_dyn = document.querySelector("#dynamic-question");
	q_dyn.innerHTML = "";
	for(var i = 0; i < questions.length; i++)
		ui_question(questions[i]);
}

var local_questions = {};
var local_answers = {};

function watch_question(ev) {
	var answer_id = ev.target.id;
	var params = answer_id.split('-');
	var question = params[1];
	var answer = parseInt(params[3]);
	var operation = "";
	var answer_value = local_questions[question][answer];
	//console.log(answer_id);
	if(ev.target.type == "radio"){
		operation = "=";
	}else{
		operation = ev.target.checked ? '+' : '-';
	}
	update_question(operation, question, answer_value)
}

function update_question(operation, question, answer){
	console.log(operation, question, answer);
	if(operation == '='){
		local_answers[question] = answer;
	}else{
		if(!Array.isArray(local_answers[question]))
			local_answers[question] = [];
		if(operation == '+')
			local_answers[question].push(answer);
		else if(operation == '-'){
			const index = local_answers[question].indexOf(answer, 0);
			if (index > -1) {
				local_answers[question].splice(index, 1);
			}
		}
	}
	client.send_answer(operation, question, answer);
	console.log(local_answers);
}

var local_rooms = {};

var room_backlog = [];
var rooms_loaded = false;

function ui_rooms(rooms){
	if(!rooms_loaded){
		room_backlog.push(rooms);
		return;
	}
	// Fixme : don't refresh
	var roomSelector = document.querySelector("#roomSelector");
	var lastSel;
	for (let index = 0; index < rooms.length; index++) {
		const room = rooms[index];
		if(room['inside'])
			lastSel = index;
		var option = document.createElement("option");
		option.value = room['id'];
		option.appendChild(document.createTextNode(room['name']));
		roomSelector.appendChild(option);
		console.log(roomSelector);
		console.log(option);
	}
}

function ui_question(question){
	/********************
	question{
		"id" : uid,
		"question" : question,
		"multiple" : true/false,
		"answers" : [
		"réponse 1",
		"réponse 2",
		"réponse 3",
		"réponse 4",...
		]
	}
	********************/
	var main_div = document.querySelector("#dynamic-question");
	var id = question['id'];
	var question_header = ons._util.createElement("<ons-list-header>" + question['question'] + "</ons-list-header>");
	//var button = ons._util.createElement("<ons-button></ons-button>");
	var answer_list = ons._util.createElement("<ons-list></ons-list>");
	main_div.appendChild(question_header);
	var multiple = question['multiple'];
	local_questions[id] = [];
	for(var i = 0; i < question['answers'].length; i++){
		var answer = question['answers'][i];
		var answer_listitem = ons._util.createElement("<ons-list-item tappable></ons-list-item>");
		var answer_checkbox;
		if(multiple){
			answer_checkbox = ons._util.createElement('<ons-checkbox input-id="question-' + id + '-answer-'+ i +'"></ons-checkbox>');
		}else{
			answer_checkbox = ons._util.createElement('<ons-radio name="question-' + id + '" input-id="question-' + id + '-answer-'+ i +'"></ons-radio>');
		}
		answer_checkbox.addEventListener('click', watch_question);
		var label = document.createElement('label');
		label.className = "left";
		label.appendChild(answer_checkbox);
		answer_listitem.appendChild(label);
		label = document.createElement('label');
		label.className = "center";
		label.htmlFor = "answer-" + i;
		label.appendChild(document.createTextNode(answer));
		local_questions[id].push(answer);
		answer_listitem.appendChild(label);
		main_div.appendChild(answer_listitem);
	}
	/*question_div.appendChild(answer_list);
	return question_div;*/
}

document.addEventListener('init', function (event) {
	var page = event.target;
	console.log("init event for ",page.id);
	if (page.id === 'login') {
		page.querySelector('#push-button').onclick = function () {
			var name = document.getElementById('name').value;
			var firstname = document.getElementById('firstname').value;
			var password = document.getElementById('password').value;
			client.identify(name, firstname, password);
		};
	} else if (page.id === 'page2') {
		
	} else if (page.id === 'main') {
		rooms_loaded = true;
		for (let index = 0; index < room_backlog.length; index++) {
			const element = room_backlog[index];
			ui_rooms(element);
		}
		room_backlog.length = 0;
	}
});

var client;

function start_client() {
	client = new Client("ws://"+window.location.hostname+":8081");
	client.attach_ui('error', ui_error);
	client.attach_ui('login', ui_login);
	client.attach_ui('kick', ui_kick);
	client.attach_ui('rooms', ui_rooms);
	client.attach_ui('disconnect', ui_disconnect);
	client.connect();
}

start_client();