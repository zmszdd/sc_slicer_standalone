; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6262d713_cross_chain_message_arrived () Bool)
(declare-fun c6262d713_lzreceive_reverted () Bool)
(declare-fun c6262d713_recipient_is_blacklisted () Bool)
(assert
 (= c6262d713_cross_chain_message_arrived c6262d713_cross_chain_message_arrived))
(assert
 (= c6262d713_lzreceive_reverted c6262d713_lzreceive_reverted))
(assert
 (= c6262d713_recipient_is_blacklisted c6262d713_recipient_is_blacklisted))
(define-fun report_preconditions () Bool (and c6262d713_recipient_is_blacklisted c6262d713_cross_chain_message_arrived))
(define-fun report_safety () Bool (=> (and c6262d713_cross_chain_message_arrived
         c6262d713_recipient_is_blacklisted)
    (not c6262d713_lzreceive_reverted)))
(define-fun report_effects () Bool (and c6262d713_cross_chain_message_arrived
     c6262d713_recipient_is_blacklisted
     (not (not c6262d713_lzreceive_reverted))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
