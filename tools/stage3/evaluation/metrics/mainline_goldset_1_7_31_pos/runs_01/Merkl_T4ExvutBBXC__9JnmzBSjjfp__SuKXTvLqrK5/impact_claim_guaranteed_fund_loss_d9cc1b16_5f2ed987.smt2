; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c76f242b9_fot_rejected_or_documented_before_whitelist () Bool)
(declare-fun c76f242b9_fot_token_is_whitelisted_reward_token () Bool)
(declare-fun c76f242b9_fund_loss_occurred () Bool)
(declare-fun c76f242b9_transfer_received_amount () Int)
(declare-fun c76f242b9_transfer_requested_amount () Int)
(assert
 (= c76f242b9_fot_rejected_or_documented_before_whitelist c76f242b9_fot_rejected_or_documented_before_whitelist))
(assert
 (= c76f242b9_fot_token_is_whitelisted_reward_token c76f242b9_fot_token_is_whitelisted_reward_token))
(assert
 (= c76f242b9_fund_loss_occurred c76f242b9_fund_loss_occurred))
(assert
 (= c76f242b9_transfer_received_amount c76f242b9_transfer_received_amount))
(assert
 (= c76f242b9_transfer_requested_amount c76f242b9_transfer_requested_amount))
(define-fun report_preconditions () Bool (and c76f242b9_fot_token_is_whitelisted_reward_token
     (< c76f242b9_transfer_received_amount c76f242b9_transfer_requested_amount)))
(define-fun report_safety () Bool (=> c76f242b9_fot_token_is_whitelisted_reward_token
    c76f242b9_fot_rejected_or_documented_before_whitelist))
(define-fun report_effects () Bool (and c76f242b9_fot_token_is_whitelisted_reward_token
     (not c76f242b9_fot_rejected_or_documented_before_whitelist)
     c76f242b9_fund_loss_occurred))
