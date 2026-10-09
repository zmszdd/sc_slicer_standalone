; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun decimals_reported () Int)
(declare-fun underlying_decimals () Int)
(declare-fun decimals_offset () Int)
(declare-fun shares_decimals () Int)
(assert
 (= decimals_reported decimals_reported))
(assert
 (= underlying_decimals underlying_decimals))
(assert
 (= decimals_offset decimals_offset))
(assert
 (= shares_decimals shares_decimals))
(define-fun report_preconditions () Bool (and (= 6 underlying_decimals) (= 6 decimals_offset) (= 6 decimals_reported)))
(define-fun report_safety () Bool (=> (= shares_decimals (+ underlying_decimals decimals_offset))
    (=> (and (= 6 underlying_decimals) (= 6 decimals_offset))
        (= decimals_reported shares_decimals))))
(define-fun report_effects () Bool (and (= shares_decimals (+ underlying_decimals decimals_offset))
     (= 6 underlying_decimals)
     (= 6 decimals_offset)
     (not (= decimals_reported shares_decimals))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
