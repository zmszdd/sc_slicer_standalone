; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun fee_index () Int)
(declare-fun max_packable_index () Int)
(declare-fun index_15_accessible () Bool)
(assert
 (= fee_index fee_index))
(assert
 (= max_packable_index max_packable_index))
(assert
 (= index_15_accessible index_15_accessible))
(define-fun report_preconditions () Bool (and (<= 15 max_packable_index) (= 16 max_packable_index) (= 15 fee_index)))
(define-fun report_safety () Bool (=> (and (= 15 fee_index) (<= 15 max_packable_index)) index_15_accessible))
(define-fun report_effects () Bool (and (= 15 fee_index) (<= 15 max_packable_index) (not index_15_accessible)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
