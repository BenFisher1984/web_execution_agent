You are my highly experienced software engineer, who has extensive experience working with institutional grade broker/execution platforms. You have extensive experience working with the Interactive Brokers API and have a proven ability to build programs that ensure speed of execution without compromising reliability. Remember, we are building an execution program that thousands of traders will use within a SaaS framework. Given real money is at stake, errors in the code/logic/framework would essentially terminate the projects future given the reputational damage and loss of actual real money. 

I would like to perform a review of the backend/engine files (attached) which have just been upgraded to improve speed of execution without compromising reliability/safety. I understand, there are many other aspects to reviewing this program, including security, maintenance, logging etc however for now I want to focus on speed, reliability and scalability, particularly given we are just about to implement dynamic contingent orders. 

I also want to ensure my understanding (as the tech entrepreneur) is consistent with your understanding of the existing logic/architecture. Essentially, are my expectations consistent with the existing logic? To perform this reconciliation, I am going to describe what I perceive to be the existing functionality, and I want you to reconcile these expectations against what is written into the code. If there are any aspects that can be enhanced at any point, please share your viewpoints.
Phase 1: User enters the order details in the GUI and “Activates” the order details. This can only occur once the order details pass the validation test (validation.py). If the order details pass the validation test the Order moves from a “draft” status and the details are saved down to the saved_trades.json. Once an Order passes the validation check, the order is immediately submitted to backend engine and the conditional orders are monitored in real-time (tick basis). At this point the broker is unaware of the conditional order. 

Order Status = Active
Trade Status = Pending 
Saved_trades.json = updated with all order details

Phase 2: When the trade_manager.py file observes an entry order that is triggered, the trade_manager.py file immediately sends a “Market” order to the order_executor.py

Order Status = Entry Order Submitted
Trade Status = Pending 
Saved_trades.json = updated to reflect the change in order status

Entrepreneurs comments/questions: is the saved_trades.json updated at this point? Is this the correct workflow that is consistent with speed and reliability? It is important the user is aware of the change of condition but equally we don’t want to compromise speed. 

Phase 3: Once the order_executor.py has executed the trade, the ACTUAL trade FILL details are then passed back to the trade_manager.py and the contingent orders (if available – which are read directly from the saved_trades.json) are immediately monitored by the trade_manager BUT are not sent to the order_executor/broker. The saved_trades.json file is updated accordingly. Live risk and Live PNL calculations are now also “turned on” given the trade is now live and has market risk implications. 

Order Status = Contingent Order Active 
Trade Stats = Live
Saved_trades.json = updated with trade details, order and trade status

Phase 4: The trade manager, is actively assessing which stop is considered “Active”. The current and only logic is to assign the highest stop as the active stop given the assumption is the trade is a long position. The trade_manager is reviewing both the active stop and whether the contingent orders have hit their targets, in real-time on a tick-by-tick basis. While this monitoring is occurring, nothing changes in the saved_trades.json. 

Phase 5: A contingent order level is hit and the trade_manager.py immediately sends the relevant order to the order_executor.py.

Order Status = Contingent Order submitted
Trade Status = Live
Saved_trades.json = Order status updated

Phase: 6: Only when the contingent order is FILLED, does the trade_manger cancel the other contingent orders and the Order Status and Trade Status are updated. The trade_manager uploads the trade details to the saved_trades.json

Order Status = Inactive 
Trade Status = Closed
Saved_trades.json = updated with trade details and respective order/trade status

This is my understanding and I want you to tell me where I am wrong. Some key aspects, I also want you to confirm

1. The GUI is always updated (i.e. the user is always aware of the order status because the saved_trades.json is updated when the status changes
2. The saved_trades.json is not unnecessarily updated too often which slows down performance?
3. An order moves from pending to Live ONLY when the order_executor has confirmed the actual FILL. The quantity is the actual quantity, not the order quantity (in case of partial fills)
4. An order moves from love to closed ONLY when the order_executor has confirmed the actual FILL. The quantity is the actual quantity, not the order quantity (in case of partial fills)




