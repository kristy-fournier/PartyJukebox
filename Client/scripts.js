let ip
let alertTime = 2
async function alertText(text="Song Added!") {
    alertbox = document.getElementById("alert");
    alertbox.innerHTML = text;
    await new Promise(r => setTimeout(r, alertTime*1000));
    alertbox.innerHTML = ""
}
// a lot of this is kinda waffly because i was trying to get 
// it to return the right stuff and javascript is asyrcronouse (boo)
async function getFromServer(bodyInfo, source="") {
    try{
        const response = await fetch("http://"+ip+"/"+source, {
            method: "POST",
            body: JSON.stringify(bodyInfo),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
            });
        const data = await response.json();
        return await data;
    } catch(e) {
        if (e == "TypeError: Failed to fetch"){
            alertText("error: NoConnect to Server (is the ip set?)")
        } else {
            alertText("error: " + e)
        }
        const response=null;
        return response;
    }
}


//cookie reader is taken from internet because cookies ae too complicated for me
//i still understand how it works though promise just i see no reason to write this from scratch
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
    }
//someone more organised than me would have set all these elements to variables so they dont have to get them 50 times
async function controlButton(buttonType) {
    if (buttonType == "pp") {
        getFromServer({control: "play-pause"}, "controls")
    } else if (buttonType == "sk") {
        getFromServer({control: "skip"}, "controls")
        if (document.getElementById("playlist-mode").style.display == "block") {
            generateVisualPlaylist("skip-button");
        }
    } else if (buttonType == "pl") {
        document.getElementById("songlist").innerHTML = "";
        document.getElementById("playlist").innerHTML = "<h1 id=\"playlist-alert\"></h1>";
        document.getElementById("playlist-mode").style.display = "block";
        document.getElementById("songlist-mode").style.display = "none";
        document.getElementById("settings-mode").style.display = "none";
        generateVisualPlaylist();
    } else if (buttonType == "se") {
        document.getElementById("songlist").innerHTML = "<h1>Search to find songs!</h1>";
        document.getElementById("playlist").innerHTML = "";
        document.getElementById("playlist-mode").style.display = "none";
        document.getElementById("songlist-mode").style.display = "block";
        document.getElementById("settings-mode").style.display = "none";
    } else if (buttonType == "st") {
        document.getElementById("songlist").innerHTML = "";
        document.getElementById("playlist").innerHTML = "";
        document.getElementById("playlist-mode").style.display = "none";
        document.getElementById("songlist-mode").style.display = "none";
        document.getElementById("settings-mode").style.display = "block";
        checkSettings()
    } else if (buttonType = "pm") {
        await getFromServer({setting: "partymode-toggle"}, "settings")
        checkSettings(true)
    }
    

}

function searchSongsEnter(e) {
    if (e.keyCode == 13) {
        searchSongs(document.getElementById("songsearch").value)
    }
}

async function searchSongs(searchTerm){
    let optionslist = []

    document.getElementById("songlist").innerHTML = ""
    searchResults = await getFromServer({search:searchTerm},"search").then()
    for (let index in searchResults) {
        optionslist.push([index,searchResults[index][0],searchResults[index][1],searchResults[index][2]]);
    }
    //generate the visual song list
    for(let i = 0; i < optionslist.length; i++) {
        let newItem = document.createElement("div");
        newItem.className = "item";
        newItem.id = optionslist[i][3];
        let image = document.createElement("img");
        try {
            if (optionslist[i][2] == null) {
                throw "no image lolz"
            }
            image.src = optionslist[i][2];
        } catch(err){
            image.src = "./images/placeholder.png";
        }
        image.id = String(optionslist[i][3])+" image";
        let head3 = document.createElement("h3");
        head3.innerText = optionslist[i][0];
        let head4 = document.createElement("h4");
        head4.innerText=optionslist[i][1];
        newItem.appendChild(image);
        newItem.appendChild(head3);
        newItem.appendChild(head4);
        document.getElementById("songlist").appendChild(newItem);
    //display error if no results
    
    } 
    if (optionslist.length == 0) {
        document.getElementById("songlist").innerHTML = "<h1>We might not have that one...</h1>";
    }
}
function alertTimeEnter(e){
    if (e.key == "Enter") {
        e.preventDefault(); 
        alertTimeSet(document.getElementById("alerttimetextbox").value);
    }
}

function alertTimeSet(time) {
    alertTime = time;
    document.cookie = "alertTime="+alertTime+"; path=/;"
    alertText("Alerts stay on screen for " + alertTime.toString() + " seconds")
}

function ipSetEnter(e){
    if (e.key == "Enter") {
        e.preventDefault(); 
        ipSetter(document.getElementById("iptextbox").value)
    }
}

function ipSetter(){
    ipBox = document.getElementById("iptextbox").value
    if (ipBox == "") {
        alertText("Your IP is set to "+ip)
    } else {
        if (ipBox.includes(":")) {
            port = ipBox.slice(ipBox.indexOf(":")+1)
            ip = ipBox;
            document.cookie = "ip="+ip+"; path=/;"
            alertText("Your IP is now set to "+ip.slice(0, ipBox.indexOf(":"))+" at port "+port)
        } else {
            ip = ipBox + ":19054"
            document.cookie = "ip="+ip+"; path=/;"
            alertText("Your IP is now set to "+ipBox+" at port 19054 (Default)")
        }
    }
        
}

async function checkSettings(skipServer=false) {
    //check client stuff first so if the server doesn't exist it can still be changed and seen
    if (ip.slice(-5)=="19054") {
        document.getElementById("iptextbox").value = ip.slice(0,-6)
    } else {
        document.getElementById("iptextbox").value = ip;
    }
    document.getElementById("alerttimetextbox").value = alertTime
    partyButtonState = document.getElementById("partymode-button").innerHTML;
    x = await getFromServer({setting: "getsettings"}, "settings");
    if (!(skipServer) || partyButtonState=="N/A") {
        if (x["partymode"] == false) {
            document.getElementById("partymode-button").innerHTML = "Off";
        } else {
            document.getElementById("partymode-button").innerHTML = "On";
        }
    } else if (document.getElementById("partymode-button").innerHTML == "Off") {
        document.getElementById("partymode-button").innerHTML = "On";
    } else {
        document.getElementById("partymode-button").innerHTML = "Off";
    }
    document.getElementById("volumerange").value = parseInt(x["volume"])
}

async function generateVisualPlaylist(conditions="") {
    document.getElementById("playlist").innerHTML = "<h1 id=\"playlist-alert\"></h1>";
    playlist = await getFromServer(null, "playlist");
    if (playlist.length==0){
        document.getElementById("playlist-alert").innerHTML = "Nothing's Queued..."
    } else {
        if (conditions=="skip-button") {
            playlist.shift()
            if (playlist.length==0){
                document.getElementById("playlist-alert").innerHTML = "Nothing's Queued..."
            }
        }
        for (i in playlist) {
            let newItem = document.createElement("div");
            newItem.className = "item";
            newItem.id = playlist[i]["file"];
            let image = document.createElement("img");
            try {
                if (playlist[i]["art"] == null) {
                    throw "no image lolz"
                }
                image.src = playlist[i]["art"];
            } catch(err){
                image.src = "./images/placeholder.png";
            }
            image.id = String(playlist[i]["file"])+" image";
            let head3 = document.createElement("h3");
            head3.innerText = playlist[i]["title"];
            let head4 = document.createElement("h4");
            head4.innerText=playlist[i]["artist"];
            let head5 = document.createElement("h5");
            let timeLeft =document.createElement("h5");
            timeLeft.style.fontWeight = 100;
            try {
                if (i == 0) {
                    head5.innerHTML="Playing";
                    if ((conditions != "skip-button")) {
                        let mins = Math.floor(playlist[i]["time"]/60);
                        let secs = Math.floor(playlist[i]["time"]%60);
                        let durMins = Math.floor(playlist[i]["length"]/60);
                        let durSecs = Math.floor(playlist[i]["length"]%60);
                        timeLeft.innerHTML = mins.toString() +":"+ secs.toLocaleString('en-US', {minimumIntegerDigits: 2,useGrouping: false}) + "/"+ durMins.toString()+":"+durSecs.toLocaleString('en-US', {minimumIntegerDigits: 2,useGrouping: false});
                    }
                }
            }catch(err){
                console.log(err)
            }
            let textdiv = document.createElement("div")
            textdiv.className="text"
            newItem.appendChild(image);
            textdiv.appendChild(head3);
            textdiv.appendChild(head4);
            textdiv.appendChild(timeLeft);
            textdiv.appendChild(head5);
            newItem.appendChild(textdiv);
            document.getElementById("playlist").appendChild(newItem);
        }
    }  
}

async function submitSong(songid) {
    getFromServer({song: songid}, "songadd")
    alertText("Added to Queue")
}
function checkWhatSongWasClicked(e) {
    itemId = e.srcElement.id;
    if ((itemId.length-itemId.lastIndexOf("image") == 5) && itemId.lastIndexOf("image")!=-1) {
        itemId = itemId.slice(0,-6)
    }
    //i feel like later dylan won't apreciate this
    //one of my files was "file.MP3" so it didn't work
    if (itemId.slice(-4).toLowerCase() == ".mp3") {
        submitSong(itemId);
    } 
}

let optionslist = []

//sets all de stuff for buttons
document.addEventListener('keydown', function(e){
    if (e.key == "/"){
    document.getElementById("title").scrollIntoView();
    document.getElementById("songsearch").select();
    e.preventDefault()
}})
document.getElementById("playlist-mode").style.display = "none";
document.getElementById("settings-mode").style.display = "none";
//.ontouch for mobile??
document.getElementById("volumerange").onchange = function() {
    getFromServer({setting:"volume",level:this.value}, "settings")
    if (this.value == 0) {
        alertText("The volume is now set to 0 (Pause?)")
    } else {
        alertText("The volume is now set to " + this.value.toString())
    }
    
}
document.getElementById("settings-button").addEventListener('click',function(){controlButton("st")});
document.getElementById("play-pause-button").addEventListener('click', function(){controlButton("pp")});
document.getElementById("playlist-button").addEventListener('click', function(){controlButton("pl")});
document.getElementById("search-button").addEventListener('click', function(){controlButton("se")});
document.getElementById("skip-button").addEventListener('click',function(){controlButton("sk")});
document.getElementById("go-search").addEventListener('click', function(){searchSongs(document.getElementById("songsearch").value)})
document.getElementById("songsearch").addEventListener('keydown', function(e){searchSongsEnter(e)});
document.getElementById("iptextbox").addEventListener('keydown', function(e){ipSetEnter(e)});
document.getElementById("alerttimetextbox").addEventListener('keydown', function(e){alertTimeEnter(e)});
document.getElementById("partymode-button").addEventListener('click',function(){controlButton("pm")})
//sets the fact that clicking a song needs to return its id to the function to find it
document.getElementById("songlist").addEventListener('click', function(e){checkWhatSongWasClicked(e)});
//makes the controls look mostly normal on all screens, best solution i could find, idk man
let tempWidth = document.getElementById('controls').clientWidth;
document.getElementById("controls").style.marginLeft = "-"+String(parseInt(tempWidth/2))+"px";
//for my use case (my immediate family), they dont know how to set an ip
//using this allows the creator of the link for, a qr code for example, to set the ip before distributing the code, and it would all work smoothly
//example (http://192.168.1.100:8000/?ip=192.168.1.100:19054 sets the ip to the same host at the default port)
//the port must be set manually using this method, but only has to be done once for the url that ends up being shared
let params = new URLSearchParams(location.search);
//tries the url first, then the cookie, then the default
ip = params.get("ip")
if (ip == null || ip=="") {
    ip=getCookie("ip")
}
console.log(ip)
if (ip==null || ip==""){
    ip = ""
}
document.cookie = "ip="+ip+"; path=/;"


alertTime = getCookie("alertTime")
document.getElementById("alerttimetextbox").value = alertTime
if (alertTime == "") {
    alertTime = 2;
    document.cookie = "alertTime="+alertTime+"; path=/;"
}