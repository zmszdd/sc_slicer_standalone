; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2d4482c5_decimals_offset () Int)
(declare-fun c2d4482c5_implied_share_decimals () Int)
(declare-fun c2d4482c5_listed_in_other_protocol () Bool)
(declare-fun c2d4482c5_published_decimals () Int)
(declare-fun c2d4482c5_underlying_decimals () Int)
(assert
 (= c2d4482c5_decimals_offset c2d4482c5_decimals_offset))
(assert
 (= c2d4482c5_implied_share_decimals c2d4482c5_implied_share_decimals))
(assert
 (= c2d4482c5_listed_in_other_protocol c2d4482c5_listed_in_other_protocol))
(assert
 (= c2d4482c5_published_decimals c2d4482c5_published_decimals))
(assert
 (= c2d4482c5_underlying_decimals c2d4482c5_underlying_decimals))
(define-fun report_preconditions () Bool (and (= 6 c2d4482c5_decimals_offset)
     (= 6 c2d4482c5_underlying_decimals)
     (= 6 c2d4482c5_published_decimals)))
(define-fun report_safety () Bool (=> (= c2d4482c5_implied_share_decimals
       (+ c2d4482c5_underlying_decimals c2d4482c5_decimals_offset))
    (=> c2d4482c5_listed_in_other_protocol
        (=> c2d4482c5_listed_in_other_protocol
            (= c2d4482c5_published_decimals c2d4482c5_implied_share_decimals)))))
(define-fun report_effects () Bool (and (= c2d4482c5_implied_share_decimals
        (+ c2d4482c5_underlying_decimals c2d4482c5_decimals_offset))
     c2d4482c5_listed_in_other_protocol
     c2d4482c5_listed_in_other_protocol
     (not (= c2d4482c5_published_decimals c2d4482c5_implied_share_decimals))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
