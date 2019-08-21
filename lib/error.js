module.exports = (err_json) => {

    if(typeof err_json != 'object')
        throw 'band-api/error.js::handle(err_json) parameter is not object';
    
    if(err_json.result_code === 1) return false;

    console.error(`Error code: ${err_json.result_code}; ${err_json.result_data.message}`);
    return true;
};