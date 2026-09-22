; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun zero_address () ReportAddress)
(declare-fun transfer_to () ReportAddress)
(declare-fun owner_has_approval () Bool)
(declare-fun nft_attached () Bool)
(declare-fun nft_voted () Bool)
(declare-fun id_owner_after () ReportAddress)
(assert
 (= zero_address zero_address))
(assert
 (= transfer_to transfer_to))
(assert
 (= owner_has_approval owner_has_approval))
(assert
 (= nft_attached nft_attached))
(assert
 (= nft_voted nft_voted))
(assert
 (= id_owner_after id_owner_after))
(define-fun report_preconditions () Bool (and owner_has_approval (not nft_attached) (not nft_voted)))
(define-fun report_safety () Bool (=> (and owner_has_approval (= transfer_to zero_address))
    (not owner_has_approval)))
(define-fun report_effects () Bool (and owner_has_approval (= transfer_to zero_address) owner_has_approval))
