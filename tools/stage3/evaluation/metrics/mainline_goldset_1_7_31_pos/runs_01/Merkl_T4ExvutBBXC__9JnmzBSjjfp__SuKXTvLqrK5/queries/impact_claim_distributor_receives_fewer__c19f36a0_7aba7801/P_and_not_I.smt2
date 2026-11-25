; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c49f40dcc_amount_actually_received () Int)
(declare-fun c49f40dcc_amount_recorded_for_pull () Int)
(declare-fun c49f40dcc_distributor_received_tokens () Int)
(declare-fun c49f40dcc_distributor_recorded_tokens () Int)
(declare-fun c49f40dcc_fot_fee_deducted_on_transfer_flag () Bool)
(declare-fun c49f40dcc_fot_token_whitelisted_flag () Bool)
(assert
 (= c49f40dcc_amount_actually_received c49f40dcc_amount_actually_received))
(assert
 (= c49f40dcc_amount_recorded_for_pull c49f40dcc_amount_recorded_for_pull))
(assert
 (= c49f40dcc_distributor_received_tokens c49f40dcc_distributor_received_tokens))
(assert
 (= c49f40dcc_distributor_recorded_tokens c49f40dcc_distributor_recorded_tokens))
(assert
 (= c49f40dcc_fot_fee_deducted_on_transfer_flag c49f40dcc_fot_fee_deducted_on_transfer_flag))
(assert
 (= c49f40dcc_fot_token_whitelisted_flag c49f40dcc_fot_token_whitelisted_flag))
(define-fun report_preconditions () Bool (and c49f40dcc_fot_token_whitelisted_flag
     c49f40dcc_fot_fee_deducted_on_transfer_flag))
(define-fun report_safety () Bool (=> c49f40dcc_fot_token_whitelisted_flag
    (= c49f40dcc_amount_recorded_for_pull c49f40dcc_amount_actually_received)))
(define-fun report_effects () Bool (and c49f40dcc_fot_token_whitelisted_flag
     (not (= c49f40dcc_amount_recorded_for_pull
             c49f40dcc_amount_actually_received))
     (< c49f40dcc_distributor_received_tokens
        c49f40dcc_distributor_recorded_tokens)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
