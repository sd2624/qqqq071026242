const funcQueues = [];

module.exports = {
    inqueue: (func, callbackFunc, ...params) => {
        if(typeof func !== 'function' || typeof callbackFunc !== 'function' || typeof params !== 'object') 
            return false;
    
        funcQueues.push([func, callbackFunc, params]);
        return true;
    },

    dequeues: () => {
        if(funcQueues.length > 0) {
            let queueSize = funcQueues.length;
            for(let i = 0; i < queueSize; i++) {
                let funcArr = funcQueues.shift();
                funcArr[0](funcArr[1], ...funcArr[2]);
            }
        }
    }
};