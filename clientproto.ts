
class Client {
	url : string;
	websocket : WebSocket;
	ui : Object;
	kick_fuse : boolean;
	timeOutHandle : number;


	constructor(url:string) {
		this.url = url;
		this.ui = {};
		this.kick_fuse = false;
	}

	on_connect(){
		return;
		///TODO:FIXME
		var ref = this;
		setInterval(function(){
			ref.__ping();
		}, 5000);
	}

	sendCommand(cmd:object){
		this.websocket.send(JSON.stringify(cmd));
	}

	on_login(){
		this.sendCommand({'cmd':'list'})
		this.ui['login']();
	}

	__pong(){
		clearTimeout(this.timeOutHandle);
	}

	__ping(){
		console.log(this);
		var ref = this;
		this.sendCommand({'cmd':'ping'})
		this.timeOutHandle = setTimeout(function(){
			ref.disconnect();
		},3000);
	}

	disconnect() {
		if(!this.kick_fuse)
			this.ui['disconnect'];
	}

	connect(){
		var ref = this;
		this.websocket = new WebSocket(this.url);
		this.websocket.onopen = function(ev:Event){
			ref.on_connect();
		}

		this.websocket.onclose = function(ev:CloseEvent){
			
		}
		this.websocket.onerror = function(ev:Event){
			ons.notification.alert('An error ocurred.');
		}

		this.websocket.onmessage = function(ev:MessageEvent){ 
			console.log(ev.data);
			var message = JSON.parse(ev.data);
			ref.handle_message(message);
		}
	}

	handle_message(message){
		if('event' in message){
			switch (message['event']) {
				case "pong":
					this.__pong();
					break;
				case "login":
					this.on_login();
					break;
				case "kick":
					this.kick_fuse = true;
					this.ui['kick']();
					break;
				default:
					console.log("Unhandled event", message['event']);
					break;
			}
		}else if('error' in message){
			this.ui['error'](message['error']);
		}else if('rooms' in message){
			console.log(message['rooms'])
			this.ui['rooms'](message['rooms']);
		}else{
			console.log("Unhandled message", message);
		}
	}

	send_answer(operation, question, answer){
		this.websocket.send(JSON.stringify({'cmd':'answer', 'op':operation, 'question':question, 'answer':answer}));
	}

	attach_ui(event_name:string, func:Function){
		this.ui[event_name] = func;
	}

	identify(name:string, first_name:string, password:string){
		this.websocket.send(JSON.stringify({'cmd' : 'identify', 'name':name, 'first_name':first_name, "password": password}));
	}

}
