; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun amount_in_base () Int)
(declare-fun quote_amount () Int)
(declare-fun revert_occurred () Bool)
(declare-fun base_token_amount_received () Int)
(declare-fun quote_token_amount_sent () Int)
(assert
 (= amount_in_base amount_in_base))
(assert
 (= quote_amount quote_amount))
(assert
 (= revert_occurred revert_occurred))
(assert
 (= base_token_amount_received base_token_amount_received))
(assert
 (= quote_token_amount_sent quote_token_amount_sent))
(define-fun report_preconditions () Bool (and (= 1 amount_in_base)
     (= 2 quote_amount)
     (distinct 0 base_token_amount_received)
     (distinct 0 quote_token_amount_sent)))
(define-fun report_safety () Bool (=> (and (= 1 amount_in_base)
         (= 2 quote_amount)
         (distinct 0 base_token_amount_received)
         (distinct 0 quote_token_amount_sent))
    (not revert_occurred)))
(define-fun report_effects () Bool (and (= 1 amount_in_base)
     (= 2 quote_amount)
     (distinct 0 base_token_amount_received)
     (distinct 0 quote_token_amount_sent)
     (not (not revert_occurred))))
(assert report_preconditions)
(check-sat)
(get-model)
