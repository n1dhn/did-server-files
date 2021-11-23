var express = require('express')
const cors = require('cors')
const bodyParser = require('body-parser')
const morgan = require('morgan')
var fs = require('fs')
var app = express()
var dataTablePath = "dataTable.json"
var async = require("async")
var lock = false 
var port = 9090

app.use(cors())
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({extended: true}))
app.use(morgan('dev'))

/**
 * Description : Used to check if the dataTable is created or not, if file is not available, it is 
 * generated and initialized.
 * Input : NA
 * Output: NA
 */
fs.writeFile(dataTablePath, "[]", { flag: 'wx' }, function (err) {
    if (err) 
        console.log("Log file already initialized")
    else
        console.log("Initialized logfile")
})


/**
 * Description : Used to fetch the level of the next token to be mined.
 * Input : None
 * Output: First record from the mine.json file.
 * Output Format : JSONObject
 * Example: {"level":2,"token":25777}
 */
app.get('/getlevel',(req,res)=>{ // for getting level of token, used for mining for computing credits at client side using level
	while(lock>0)
        console.log("locked "+ lock)
	lock++
	console.log("lock acquired "+lock)
	let miningdata = fs.readFileSync("mine.json", 'utf8')
    let mineparsed = JSON.parse(miningdata)
	lock--
	console.log("unlocked "+lock)
    res.end(JSON.stringify(mineparsed[0]))
	
})

/**
 * Description : Used to fetch the details of the next token to be mined. The record is deleted from the 
 * file as the record's corresponding token is mined.
 * Input : None
 * Output: First record from the mine.json file.
 * Output Format : JSONArray
 * Example: [{"level":2,"token":25777}]
 */
app.get('/minetoken',(req,res)=>{ // for mining the token, returning next token to be mined and delete from file
    while(lock>0)
        console.log("locked "+ lock)
    lock++
    console.log("lock acquired "+lock)
    var records = fs.readFileSync("mine.json")
    var mineparsed = JSON.parse(records)
    var sendback = mineparsed.slice(0,1)
    var writeback = mineparsed.slice(1,mineparsed.length)
    fs.writeFileSync("mine.json", JSON.stringify(writeback))
    lock--
    console.log("unlocked "+lock)
    res.send(sendback)

})

app.get('/updateTxn',(req, res)=>{
    var responseData = {
      "success": true
    }
    res.end( JSON.stringify(responseData));
  })

/**
 * Description : Used to check if the server is running.
 * Input : None
 * Output: Status that server is running.
 * Output Format : String
 * Example: running
 */
app.get('/test',(req,res)=>{ //server running or not
console.log("tested")
res.end("running")
})

/**
 * Description : Used to fetch the details of all the nodes in the network.
 * Input : None
 * Output: All record from dataTable.json file.
 * Output Format : JSONArray
 * Example: [{"peerid":"Qmb9ghACUGzLYueVea3ihHaKtU6doJrj8swffkP9CZkGbT","didHash":"QmW8e8XMd9gmkGgxgsgPWEhkKLuE4o4TFhvKXyLAELBRYu",
 * "walletHash":"QmPHo6Aopr4nhVEaSBBYE9kdcPCrBaU84XJkzvyCQAu7pG"},{"peerid":"QmQEftV3oU7sWpxitiTHK5J8BSSVV7KNP9xbixqDqLu9qj",
 * "didHash":"QmfWAwbWmR51k8gV1AY12qMV3X9h6SthmESCQm9VwPFVLx","walletHash":"Qmds8PiBQ6zj3tSmRSoGSaZMsDbKCLCakHi9K5UCZGTJ53"}]
 */
app.get('/get',(req,res)=>{ //get dataTable contents, used for /sync in client side
fs.readFile(dataTablePath,(err, data)=>{
  if (err) {
    res.writeHead(500)
    return res.end('Error loading path.json')
    }
    res.writeHead(200)
    res.end(data)
    })
})

/**
 * Description : Used to push records of new DIDs which are created into the server's dataTable.json. If 
 * a DID is recreated in a system which already has a DID, the peerIDs of the old and new records are matched
 * and corresponding DIDs and WalletIDs are replaced with the new values. 
 * Input : JSONObject
 * Input Format : JSON
 * Example : [{"peerid":"Qmb9ghACUGzLYueVea3ihHaKtU6doJrj8swffkP9CZkGbT","didHash":"QmW8e8XMd9gmkGgxgsgPWEhkKLuE4o4TFhvKXyLAELBRYu",
 * "walletHash":"QmPHo6Aopr4nhVEaSBBYE9kdcPCrBaU84XJkzvyCQAu7pG"}]
 * Output: Confirmation that records are added.
 * Output Format : String
 * Example: added
 */
app.post('/add',(req,res)=>{ //for adding the new DIDs to file, done during DID creation
    var flag = true
    var data = req.body
    var log = data[0]
    console.log(log) 

    async.waterfall([
    (callback)=>{
        fs.readFile(dataTablePath,(err,data)=>{
            if(err) throw err
            info = JSON.parse(data)
            info.forEach(function(record) {
                if(record['peerid']===log['peerid']){
					console.log("replace entry for "+log['peer-id']+" new did: "+log['did']+" old did: "+record['did'])		
                    record.didHash=log.didHash
                    record.walletHash=log.walletHash
                    flag = false
                } 
            })
            if(flag){
                info.push(log)
		        console.log("new entry for "+log['peerid']+" with did "+log['did'])		
		}
            callback(JSON.stringify(info))
        })
    }
    ],(result,err)=>{
        fs.writeFile(dataTablePath, result,(err)=>{
            if (err) throw err
            console.log("Request logged")
            res.end("added")
        })
    })  
})

/**
 * Description : Port on which server listens.
 * Input : NA
 * Output: NA
 */
app.listen(port,()=>{
    console.log('server started at',port)
})
