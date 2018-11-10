function goToNextPage() {
  if(!window.location.href.includes(`page=${ page }`))
  window.location.href = `${ window.location.href.split('?', 1)[0] }${ window.location.href.split(/\?(.+)/)[1] == undefined ? '?' : `?${ window.location.href.split(/\?(.+)/)[1] }&` }page=${ page + 1 }`
  else
  window.location.href = window.location.href.replace(`page=${ page }`, `page=${ page + 1 }`)
}

function goToPreviousPage() {
  if(!window.location.href.includes(`page=${ page }`))
  window.location.href = `${ window.location.href.split('?', 1)[0] }${ window.location.href.split(/\?(.+)/)[1] == undefined ? '?' : `?${ window.location.href.split(/\?(.+)/)[1] }&` }page=${ page - 1 }`
  else
  window.location.href = window.location.href.replace(`page=${ page }`, `page=${ page - 1 }`)
}

function search() {
  const newQuery = $('#search-input').val()
  if(!window.location.href.includes(`query=${ query }`))
  window.location.href = `${ window.location.href.split('?', 1)[0] }${ window.location.href.split(/\?(.+)/)[1] == undefined ? '?' : `?${ window.location.href.split(/\?(.+)/)[1] }&` }query=${ newQuery }`
  else
  window.location.href = window.location.href.replace(`query=${ query }`, `query=${ newQuery }`)
}

function setAdvancedSettings() {
  const newPage = $('#page-input').val()
  const newUrl = null;
  if(!window.location.href.includes(`page=${ page }`))
  newUrl = `${ window.location.href.split('?', 1)[0] }${ window.location.href.split(/\?(.+)/)[1] == undefined ? '?' : `?${ window.location.href.split(/\?(.+)/)[1] }&` }page=${ newPage }`
  else
  newUrl = window.location.href.replace(`page=${ page }`, `page=${ newPage }`)

  const newProductsPerPage = $('#products-per-page').val()
  if(!window.location.href.includes(`page=${ page }`))
  window.location.href = `${ newUrl.split('?', 1)[0] }${ newUrl.split(/\?(.+)/)[1] == undefined ? '?' : `?${ newUrl.split(/\?(.+)/)[1] }&` }products-per-page=${ newProductsPerPage }`
  else
  window.location.href = newUrl.replace(`products-per-page=${ products-per-page }`, `products-per-page=${ newProductsPerPage }`)
}

function onIdInputKeydown(event) {
  if(event.key == 'Enter' && $('#id-input').val() != '')
  goToProduct()
}

function onIdInputUpdate() {
  $('#go-to-product-button').enabled($('#id-input').val() != '')
}

function goToProduct() {
  window.location.href = `/product/${ $('#id-input').val() }/update`
}

jQuery.fn.extend({
    enabled: function(state) {
        return this.each(function() {
            this.disabled = !state;
        });
    }
});

$(document).ready(
  function onDocumentReady() {
    $('.next-page-button').click(goToNextPage)
    $('.previous-page-button').click(goToPreviousPage)
    $('#search-button').click(search)
    $('#go-to-product-button').click(goToProduct)
    $('#id-input').on('keydown', onIdInputKeydown)

    onIdInputUpdate()
    $('#id-input').on('input', onIdInputUpdate)
  }
)
