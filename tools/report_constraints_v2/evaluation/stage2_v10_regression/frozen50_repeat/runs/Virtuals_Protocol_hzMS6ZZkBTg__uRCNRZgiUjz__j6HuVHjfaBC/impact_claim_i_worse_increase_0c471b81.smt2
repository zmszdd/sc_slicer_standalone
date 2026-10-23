; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c08fdae0f_negative () Bool)
(declare-fun c08fdae0f_worse_party_rating_increased () Bool)
(assert
 (= c08fdae0f_negative c08fdae0f_negative))
(assert
 (= c08fdae0f_worse_party_rating_increased c08fdae0f_worse_party_rating_increased))
(define-fun report_preconditions () Bool (and c08fdae0f_negative (not c08fdae0f_negative)))
(define-fun report_safety () Bool (=> c08fdae0f_negative (not c08fdae0f_worse_party_rating_increased)))
(define-fun report_effects () Bool (and c08fdae0f_negative (not (not c08fdae0f_worse_party_rating_increased))))
